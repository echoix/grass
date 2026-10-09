@echo off
rem Builds bench.cpp twice against bzip2 1.0.8: with the flags the OSGeo4W
rem setup uses (CMake MinSizeRel: /O1 /Ob1) and with /O2.
setlocal enabledelayedexpansion
set WORK=%1
set HERE=%~dp0

for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -property installationPath`) do set VSDIR=%%i
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" || exit /b 1

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
    /Fo:obj_%%O\ /Fe:bench_%%O.exe || exit /b 1
)
