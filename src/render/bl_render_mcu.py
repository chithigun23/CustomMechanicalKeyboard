"""MCU assembly: real colours, white studio, final stills.
    blender --background mcu_assembly.blend --python bl_render_mcu.py
"""
import os, sys, importlib
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_studio as S, bl_materials as M
importlib.reload(S); importlib.reload(M)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
RES = (1600, 1000)
M.pcb(bpy.data.objects["MCU_Board"], mask=M.JLC_BLUE)
M.tweak_components("MCU_")

for name, az, el, lens in [("mcu_final_hero", -58, 34, 70),
                           ("mcu_final_top",  -90, 78, 60),
                           ("mcu_final_low",  -42, 15, 85)]:
    S.studio(prefix="MCU_", az=az, el=el, lens=lens, res=RES, style="white")
    S.render_settings(res=RES, samples=128)
    bpy.context.scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", name)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcu_assembly.blend"))
