MCU ASSEMBLY ANIMATION - render kit
===================================

mcu_anim.blend is self-contained. All geometry is baked in and every material is
procedural, so there are no external textures or linked files - copy this whole
folder to the desktop machine and it will render as-is.

WHAT IT IS
  250 frames, 30 fps  =  8.3 seconds, 1920x1080, EEVEE, 96 samples.
  The board sits still; 22 components fall in from above and settle, then the
  two through-hole headers (J1 and CNN1) rise up through the floor. The camera
  orbits 26 degrees across the shot.

TO RENDER
  Double-click RENDER_ON_DESKTOP.bat
  Frames go to ./frames/mcu_0001.png ... mcu_0250.png

  It is safe to stop it and run it again - finished frames are skipped, so an
  interrupted render resumes rather than starting over.

TO MAKE AN MP4
  Double-click ENCODE_MP4.bat  ->  mcu_assembly.mp4

TIMING
  This laptop managed ~17 s/frame, so about 71 minutes for the full 250.
  A 3080 should be far quicker - EEVEE is a rasteriser and uses the GPU
  automatically, no device setup needed. Expect a few minutes.

IF YOU WANT TO CHANGE ANYTHING
  Open the .blend normally. Useful things to reach for:
    - each component is a separate object named MCU_<refdes>, with two location
      keyframes (entry and landing). Drag them in the Dope Sheet to retime.
    - the camera is parented to CamPivot; its Z rotation keys are the orbit.
    - Key / Top / FillR / FillL are the four area lights.
    - render samples: Render Properties > Sampling.

  If it looks too bright or too dark, the cleanest single control is
  Render Properties > Color Management > Exposure. It is currently -0.15.
