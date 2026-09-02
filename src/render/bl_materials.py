"""Material roles for the KiCad-exported boards, plus the printed/machined parts.

KiCad's GLB export gives every board seven material slots in a fixed order:
    0,1  copper (tracks / pads)   metallic, gold by default
    2,3  silkscreen               top / bottom, thin flat overlays
    4,5  soldermask               top / bottom, flat overlays that sit 0.05
                                  above the substrate, so they are the face you
                                  actually see
    6    substrate                the FR4 body, visible at the routed edge and
                                  through mask openings
Colours below are linear (Blender working space), not sRGB.
"""
import bpy

# --- linear-space palettes -------------------------------------------------
JLC_BLUE = (0.015, 0.090, 0.420)
JLC_BLACK = (0.016, 0.017, 0.020)
JLC_GREEN = (0.020, 0.130, 0.055)
SILK_WHITE = (0.760, 0.770, 0.780)
FR4 = (0.300, 0.255, 0.150)
HASL = (0.720, 0.730, 0.755)   # lead-free HASL, JLCPCB's default finish
ENIG = (0.780, 0.620, 0.280)
ORANGE_PLA = (0.720, 0.130, 0.012)
ALU_ANODISED_BLACK = (0.030, 0.031, 0.034)
BRASS = (0.680, 0.500, 0.180)


def _bsdf(mat):
    if not mat or not mat.use_nodes:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def opaque(mat):
    """Force a material fully opaque.

    KiCad's GLB export ships the board semi-transparent so you can see inner
    layers in a viewer: soldermask alpha 0.83, silkscreen 0.90, substrate 0.98,
    all with blend mode BLEND (copper is HASHED).  Left alone the board reads as
    translucent and the bottom-side copper and via barrels show through.
    """
    b = _bsdf(mat)
    if b and "Alpha" in b.inputs:
        b.inputs["Alpha"].default_value = 1.0
        for lk in list(b.inputs["Alpha"].links):
            mat.node_tree.links.remove(lk)
    for attr, val in (("blend_method", "OPAQUE"),
                      ("surface_render_method", "DITHERED"),
                      ("shadow_method", "OPAQUE")):
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass


def set_mat(mat, color, metallic=0.0, roughness=0.5):
    b = _bsdf(mat)
    if not b:
        return
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    opaque(mat)


def pcb(obj, mask=JLC_BLUE, silk=SILK_WHITE, copper=HASL, trace_lift=1.35):
    """Recolour a KiCad board object by material-slot role.

    Roles established empirically (renders/slottest.png), not from the slot
    names, which are just mat_0..mat_6:
        0,1  exposed copper - the pads
        2,3  silkscreen - small area, sits topmost at z+0.075
        4,5  soldermask laid over copper - reads as the faint raised traces
        6    the board body - the large flat face you actually see, so this is
             the one that carries the board colour
    """
    trace = tuple(min(1.0, c * trace_lift + 0.012) for c in mask)
    roles = [(copper, 1.0, 0.32), (copper, 1.0, 0.32),
             (silk, 0.0, 0.85), (silk, 0.0, 0.85),
             (trace, 0.0, 0.30), (trace, 0.0, 0.30),
             (mask, 0.0, 0.36)]
    slots = obj.data.materials
    for i, (col, met, rough) in enumerate(roles):
        if i < len(slots) and slots[i] is not None:
            set_mat(slots[i], col, met, rough)
    return obj


def solid(obj, color, metallic=0.0, roughness=0.5, name=None):
    """Replace every slot on an object with one flat material."""
    m = bpy.data.materials.new(name or (obj.name + "_mat"))
    m.use_nodes = True
    set_mat(m, color, metallic, roughness)
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return m


def tweak_components(prefix="MCU_"):
    """Warm up the generic KiCad component colours a little.

    The vendor STEP models arrive with flat greys; nudging the plastic darker
    and the metal brighter stops everything reading as the same putty colour.
    """
    for o in bpy.data.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        if o.name.endswith("_Board"):
            continue
        for slot in o.data.materials:
            b = _bsdf(slot)
            if not b:
                continue
            opaque(slot)      # vendor STEP models arrive semi-transparent too
            c = b.inputs["Base Color"].default_value
            lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
            if lum < 0.05:                       # black IC bodies / plastics
                set_mat(slot, (0.020, 0.020, 0.022), 0.0, 0.42)
            elif c[0] > c[2] * 1.35 and lum > 0.15:   # gold-ish pins
                set_mat(slot, BRASS, 1.0, 0.30)
            elif lum > 0.45:                     # bright metal shells / cans
                set_mat(slot, (0.660, 0.670, 0.690), 1.0, 0.26)
