@echo off
REM Turn the rendered PNG sequence into an MP4 using Blender's built-in ffmpeg.
set BLENDER=
if exist "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" set BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
if "%BLENDER%"=="" for /d %%D in ("C:\Program Files\Blender Foundation\Blender *") do set BLENDER=%%D\blender.exe
"%BLENDER%" --background --python "%~dp0encode.py"
pause
