@echo off
REM Render the MCU assembly animation. Frames land in .\frames\
REM Safe to stop and re-run - finished frames are skipped and it picks up where
REM it left off (the .blend has Overwrite off and Placeholders on).

set BLENDER=
if exist "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" set BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
if "%BLENDER%"=="" for /d %%D in ("C:\Program Files\Blender Foundation\Blender *") do set BLENDER=%%D\blender.exe
if "%BLENDER%"=="" (
  echo Could not find blender.exe - edit this file and set BLENDER manually.
  pause
  exit /b 1
)

echo Using %BLENDER%
"%BLENDER%" --background "%~dp0mcu_anim.blend" -o "//frames/mcu_" -s 1 -e 250 -a
echo.
echo Done. 250 PNG frames are in %~dp0frames
pause
