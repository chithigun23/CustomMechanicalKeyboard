"""Shared studio rig for the assembly renders.  Import from a render script.

The scene is in millimetres (1 unit = 1 mm).  Blender's light energy is in watts
and assumes units are metres, so a light 45 units away is treated as 45 m away
and the inverse-square falloff makes any sane wattage invisible.  Every light
here is therefore specified as a target irradiance at the subject and the wattage
is solved from the actual distance.
"""
import math

import bpy
from mathutils import Vector

# House exposure for the white sweep.  Landed by bracketing (renders/expo_*.png):
# much above this and the backdrop clips and the blue board goes pastel.
# Making the boards opaque removed the light that used to pass through them, so
# more is bounced back and the frame sits brighter - hence the drop from -0.15.
# AgX desaturates hard by design; the Punchy look puts the colour back without
# giving up its highlight rolloff.
WHITE_INTENSITY = 0.90
WHITE_EXPOSURE = -0.45
WHITE_LOOK = "AgX - Punchy"


def bounds(prefix=None, objs=None):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    pool = objs if objs is not None else bpy.data.objects
    for o in pool:
        if o.type != "MESH":
            continue
        if prefix and not o.name.startswith(prefix):
            continue
        if o.name.startswith("Backdrop"):
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, p.x), min(lo.y, p.y), min(lo.z, p.z)))
            hi = Vector((max(hi.x, p.x), max(hi.y, p.y), max(hi.z, p.z)))
    return lo, hi


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def clear_helpers():
    for o in list(bpy.data.objects):
        if o.type in {"LIGHT", "CAMERA"} or o.name.startswith("Backdrop"):
            bpy.data.objects.remove(o, do_unlink=True)


def add_area(name, loc, target, size, irradiance, color=(1, 1, 1)):
    """irradiance is roughly W/m^2 wanted at `target`; wattage is solved for it."""
    d = bpy.data.lights.new(name, type="AREA")
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    look_at(o, target)
    dist = (Vector(target) - Vector(loc)).length
    d.energy = irradiance * 4.0 * math.pi * dist * dist
    return o


def backdrop(ctr, span, z, color=(0.05, 0.052, 0.058), roughness=0.45):
    bpy.ops.mesh.primitive_plane_add(size=span * 30, location=(ctr.x, ctr.y, z))
    g = bpy.context.active_object
    g.name = "Backdrop"
    m = bpy.data.materials.new("BackdropMat")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = roughness
    g.data.materials.append(m)
    return g


def world_color(color=(0.035, 0.037, 0.043), strength=1.0):
    w = bpy.data.worlds[0] if bpy.data.worlds else bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def frame_camera(name, ctr, radius, az_deg, el_deg, lens=70, margin=1.22,
                 res=(1600, 1000)):
    """Place a camera so a sphere of `radius` at `ctr` fills the frame."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 1.0
    cd.clip_end = 100000.0
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)

    aspect = res[0] / float(res[1])
    fov_h = 2.0 * math.atan(cd.sensor_width / (2.0 * lens))
    fov_v = 2.0 * math.atan((cd.sensor_width / aspect) / (2.0 * lens))
    fov = min(fov_h, fov_v)
    dist = radius / math.sin(fov / 2.0) * margin

    az, el = math.radians(az_deg), math.radians(el_deg)
    cam.location = (ctr.x + dist * math.cos(el) * math.cos(az),
                    ctr.y + dist * math.cos(el) * math.sin(az),
                    ctr.z + dist * math.sin(el))
    look_at(cam, ctr)
    bpy.context.scene.camera = cam
    return cam


def studio(prefix=None, objs=None, az=-58, el=34, lens=70, res=(1600, 1000),
           margin=1.22, style="white", ground_drop=0.06, intensity=WHITE_INTENSITY):
    """Backdrop + lights + framed camera around whatever matches `prefix`.

    style "white" is a bright seamless sweep: big soft toplight, two low fills
    and a bounce, so parts read as clean product shots with soft contact shadows.
    style "dark" is the charcoal studio with a warm rim.
    """
    clear_helpers()
    lo, hi = bounds(prefix, objs)
    ctr = (lo + hi) / 2.0
    span = max(hi.x - lo.x, hi.y - lo.y)
    radius = (hi - lo).length / 2.0
    k = span
    tgt = (ctr.x, ctr.y, ctr.z)
    gz = lo.z - span * ground_drop

    if style == "white":
        # A big bright sweep bounces a lot of light back into the subject, so the
        # backdrop albedo and the world both have to stay well under 1.0 or the
        # whole frame drifts up and clips.
        backdrop(ctr, span, gz, color=(0.50, 0.505, 0.515), roughness=0.55)
        world_color((0.20, 0.21, 0.235), 1.0)
        i = intensity
        add_area("Key",   (ctr.x - k * 0.55, ctr.y - k * 0.95, ctr.z + k * 1.85), tgt,
                 k * 2.6, 2.4 * i)
        add_area("Top",   (ctr.x, ctr.y, ctr.z + k * 2.3), tgt, k * 3.2, 1.0 * i)
        add_area("FillR", (ctr.x + k * 1.8, ctr.y - k * 0.35, ctr.z + k * 0.55), tgt,
                 k * 2.4, 0.85 * i, color=(0.95, 0.97, 1.0))
        add_area("FillL", (ctr.x - k * 1.9, ctr.y + k * 0.5, ctr.z + k * 0.5), tgt,
                 k * 2.2, 0.55 * i, color=(1.0, 0.98, 0.95))
    else:
        backdrop(ctr, span, gz, color=(0.05, 0.052, 0.058), roughness=0.45)
        world_color((0.035, 0.037, 0.043), 1.0)
        add_area("Key",  (ctr.x - k * 1.0, ctr.y - k * 1.2, ctr.z + k * 1.5), tgt,
                 k * 1.5, 5.5)
        add_area("Fill", (ctr.x + k * 1.6, ctr.y - k * 0.5, ctr.z + k * 0.6), tgt,
                 k * 2.0, 1.6, color=(0.80, 0.87, 1.0))
        add_area("Rim",  (ctr.x + k * 0.3, ctr.y + k * 1.7, ctr.z + k * 1.0), tgt,
                 k * 1.3, 3.2, color=(1.0, 0.95, 0.86))

    cam = frame_camera("Cam", ctr, radius, az, el, lens=lens, margin=margin, res=res)
    return ctr, span, radius, cam


def render_settings(engine="BLENDER_EEVEE", res=(1600, 1000), samples=96,
                    look=WHITE_LOOK, exposure=WHITE_EXPOSURE):
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = exposure
    try:
        sc.view_settings.look = look
    except TypeError:
        pass
    if engine == "BLENDER_EEVEE":
        for attr, val in (("taa_render_samples", samples), ("use_raytracing", True),
                          ("use_shadows", True)):
            if hasattr(sc.eevee, attr):
                setattr(sc.eevee, attr, val)
    elif engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
    return sc
