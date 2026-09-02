"""Build the MCU assembly animation and save a self-contained .blend.

    blender --background mcu_assembly.blend --python bl_animate_mcu.py

Components fall from above and settle onto the board; the two through-hole
headers rise from below instead, emerging through the backdrop so they read as
coming up out of the floor.  The camera orbits slowly across the whole shot.

Writes mcu_anim.blend, which has no external dependencies - all geometry is
imported and every material is procedural - so it can be copied to another
machine and rendered as-is.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_studio as S
import bl_materials as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_BLEND = os.path.join(HERE, "mcu_anim.blend")

FPS = 30
RES = (1920, 1080)
SAMPLES = 96

DROP_FRAMES = 26          # travel time for one part
DROP_H = 75.0             # start height above the landed position
RISE_H = -65.0            # headers start below the floor
IN_STAGGER = 4            # frames between parts inside a group
BIG_STAGGER = 9           # ditto for the larger parts
GROUP_GAP = 12            # pause between groups
LEAD_IN = 12              # frames of still board before anything moves
HOLD_OUT = 45             # frames after the last landing

random.seed(7)            # keep the jitter reproducible

# assembly order: small passives first, then silicon, then connectors, then
# the two headers from below
GROUPS = [
    (["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11",
      "R1", "R2", "R3", "FB1", "F1"], IN_STAGGER, DROP_H),
    (["U1", "U3", "U2"], BIG_STAGGER, DROP_H),
    (["USB1", "SW1", "SW2"], BIG_STAGGER, DROP_H),
    (["J1", "CNN1"], BIG_STAGGER + 3, RISE_H),
]


def fcurves_of(obj):
    """Blender 4.4+ moved fcurves into action layers/slots; handle both."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        if hasattr(act, "layers") and len(act.layers):
            for layer in act.layers:
                for strip in layer.strips:
                    cb = strip.channelbag(ad.action_slot, ensure=False)
                    if cb:
                        return list(cb.fcurves)
    except Exception:
        pass
    return list(act.fcurves)


def ease_out(obj, interp="QUART"):
    for fc in fcurves_of(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            kp.easing = "EASE_OUT"


def drop(obj, f_start, f_end, height):
    home = Vector(obj.location)
    obj.location = home + Vector((0, 0, height))
    obj.keyframe_insert("location", frame=f_start)
    obj.location = home
    obj.keyframe_insert("location", frame=f_end)
    ease_out(obj)
    return home


# ---------------------------------------------------------------- materials
M.pcb(bpy.data.objects["MCU_Board"], mask=M.JLC_BLUE)
M.tweak_components("MCU_")

# ---------------------------------------------------------------- studio
ctr, span, radius, cam = S.studio(prefix="MCU_", az=-70, el=32, lens=70,
                                  res=RES, style="white")
sc = S.render_settings(res=RES, samples=SAMPLES)
sc.render.fps = FPS

# ---------------------------------------------------------------- animation
t = LEAD_IN
last_land = t
placed = []
for names, stagger, height in GROUPS:
    for n in names:
        o = bpy.data.objects.get("MCU_" + n)
        if o is None:
            print("  !! missing MCU_%s" % n)
            continue
        jitter = random.randint(-1, 2)
        f0 = t + jitter
        f1 = f0 + DROP_FRAMES + random.randint(-2, 3)
        drop(o, f0, f1, height)
        placed.append((n, f0, f1))
        last_land = max(last_land, f1)
        t += stagger
    t += GROUP_GAP

END = last_land + HOLD_OUT
sc.frame_start = 1
sc.frame_end = END

# ---------------------------------------------------------------- camera move
pivot = bpy.data.objects.new("CamPivot", None)
pivot.empty_display_size = span * 0.4
pivot.location = ctr
bpy.context.scene.collection.objects.link(pivot)
bpy.context.view_layer.update()          # pivot.matrix_world must be current

# Keep the camera exactly where studio() put it.  Assigning matrix_world after
# parenting resolves against a stale parent matrix and silently collapses the
# camera onto the pivot; matrix_parent_inverse is the reliable way.
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
bpy.context.view_layer.update()

cam_d = (cam.matrix_world.translation - Vector(ctr)).length
print("camera at %s, %.1f mm from centre (subject radius %.1f)"
      % (tuple(round(v, 1) for v in cam.matrix_world.translation), cam_d, radius))
assert cam_d > radius, "camera ended up inside the subject"

pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.radians(26))
pivot.keyframe_insert("rotation_euler", frame=END)
for fc in fcurves_of(pivot):
    for kp in fc.keyframe_points:
        kp.interpolation = "SINE"
        kp.easing = "EASE_IN_OUT"

# ---------------------------------------------------------------- output
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(HERE, "frames", "mcu_")
sc.render.use_overwrite = False      # lets an interrupted render resume
sc.render.use_placeholder = True

try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("  (pack_all: %s)" % e)

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

print()
print("=== ANIMATION ===")
print("%d parts, frames 1..%d @ %d fps  =  %.1f s" % (len(placed), END, FPS, END / float(FPS)))
print("resolution %dx%d, EEVEE, %d samples" % (RES[0], RES[1], SAMPLES))
print()
for n, f0, f1 in placed:
    print("  %-6s enters f%-4d lands f%-4d" % (n, f0, f1))
print()
print("saved", OUT_BLEND)
