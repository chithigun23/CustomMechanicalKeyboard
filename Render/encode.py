"""Assemble frames/mcu_####.png into mcu_assembly.mp4 (30 fps, H.264)."""
import glob, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
frames = sorted(glob.glob(os.path.join(HERE, "frames", "mcu_*.png")))
if not frames:
    raise SystemExit("no frames found - run RENDER_ON_DESKTOP.bat first")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, len(frames)
se = sc.sequence_editor_create()
strip = se.sequences.new_image("anim", frames[0], 1, 1)
for f in frames[1:]:
    strip.elements.append(os.path.basename(f))
sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.constant_rate_factor = "HIGH"
sc.render.filepath = os.path.join(HERE, "mcu_assembly.mp4")
bpy.ops.render.render(animation=True)
print("wrote", sc.render.filepath)
