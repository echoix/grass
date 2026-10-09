@echo off
rem Builds bench.cpp twice against bzip2 1.0.8: with the flags the OSGeo4W
rem setup uses (CMake MinSizeRel: /O1 /Ob1) and with /O2.
setlocal enabledelayedexpansion
set WORK=%1
set HERE=%~dp0

rem The published osgeo4w-setup.exe is linked with MSVC 14.44 (Visual Studio
rem 2022 17.14; see build-helpers vs2022env), so use that toolset, not the
rem newest Visual Studio on the runner.
set "PATH=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer;%PATH%"
for /f "usebackq tokens=*" %%i in (`vswhere -latest -products * -version [17.0,17.99] -property installationPath`) do set VSDIR=%%i
if not defined VSDIR (
  echo Visual Studio 2022 not found
  exit /b 1
)
dir /b "%VSDIR%\VC\Tools\MSVC"
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" -vcvars_ver=14.44 || exit /b 1
cl 2>&1 | findstr /i "Version"
link 2>&1 | findstr /i "Version"

mkdir %WORK% 2>nul
cd /d %WORK%
if not exist bzip2-1.0.8 (
  curl.exe -fsSL -o bzip2.tar.gz https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz || exit /b 1
  tar xzf bzip2.tar.gz || exit /b 1
)

set BZ=bzip2-1.0.8
for %%O in (O1 O2) do (
  mkdir obj_%%O 2>nul
  if "%%O"=="O1" (set OPT=/O1 /Ob1) else (set OPT=/O2)
  cl /nologo /MT /EHsc /DNDEBUG /D_CRT_SECURE_NO_WARNINGS /wd4996 /wd4267 /wd4244 !OPT! ^
    /I%BZ% "%HERE%bench.cpp" ^
    %BZ%\bzlib.c %BZ%\crctable.c %BZ%\blocksort.c %BZ%\compress.c ^
    %BZ%\decompress.c %BZ%\huffman.c %BZ%\randtable.c ^
    /Fo:obj_%%O\ /Fe:bench_%%O.exe /link user32.lib || exit /b 1
)
