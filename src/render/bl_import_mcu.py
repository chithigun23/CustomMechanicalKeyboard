"""Blender: import the MCU daughterboard and its 24 components as named objects.

Run headless:
    blender --background --python bl_import_mcu.py

Each GLB was exported from KiCad in the same coordinate frame, so importing them
all without moving anything puts every component exactly where it belongs.

Two things the glTF importer does that have to be handled:
  * it writes metres (a 30 mm board arrives 0.03 across), so everything is
    scaled x1000 to work in millimetres
  * component placement lives on parent empties, not in the mesh vertices, so
    the parent transform must be applied before those empties are deleted
"""
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "glb")
OUT_BLEND = os.path.join(HERE, "mcu_assembly.blend")
MM = 1000.0  # glTF metres -> millimetres


def import_glb(path, name, set_origin):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        return None

    # bake the parent empties' transform into the meshes, THEN drop the empties
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if set_origin:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    return obj


def bbox_world(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


bpy.ops.wm.read_factory_settings(use_empty=True)

parts = json.load(open(os.path.join(HERE, "mcu_parts.json")))
refs = [p["ref"] for p in parts if p["model"]]

board = import_glb(os.path.join(GLB, "mcu_board.glb"), "MCU_Board", False)
if board is None:
    sys.exit("board import failed")
comps = []
for ref in refs:
    p = os.path.join(GLB, "mcu_part_%s.glb" % ref)
    if os.path.exists(p):
        o = import_glb(p, "MCU_%s" % ref, True)
        if o:
            comps.append(o)

everything = [board] + comps

# metres -> millimetres, about the world origin
bpy.ops.object.select_all(action="DESELECT")
for o in everything:
    o.select_set(True)
bpy.context.view_layer.objects.active = board
bpy.context.scene.tool_settings.transform_pivot_point = "CURSOR"
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.transform.resize(value=(MM, MM, MM), center_override=(0, 0, 0))
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# recentre: board centred on the origin in XY, its underside on Z=0
lo, hi = bbox_world(board)
shift = Vector((-(lo.x + hi.x) / 2.0, -(lo.y + hi.y) / 2.0, -lo.z))
for o in everything:
    o.location = o.location + shift
bpy.context.view_layer.update()

# tidy: one collection, board first
col = bpy.data.collections.new("MCU_Assembly")
bpy.context.scene.collection.children.link(col)
for o in everything:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)

bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 0.001  # 1 unit = 1 mm
bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"

print()
print("=== IMPORTED (millimetres) ===")
lo, hi = bbox_world(board)
print("board  size %.2f x %.2f x %.2f   at X %.2f..%.2f Y %.2f..%.2f Z %.2f..%.2f"
      % (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
print()
tot = len(board.data.vertices)
for o in comps:
    lo2, hi2 = bbox_world(o)
    tot += len(o.data.vertices)
    print("  %-12s pos (%7.2f,%7.2f,%6.2f)  size %5.2f x %5.2f x %5.2f"
          % (o.name, o.location.x, o.location.y, o.location.z,
             hi2.x - lo2.x, hi2.y - lo2.y, hi2.z - lo2.z))
print()
print("components: %d   total verts: %d" % (len(comps), tot))

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("saved", OUT_BLEND)
