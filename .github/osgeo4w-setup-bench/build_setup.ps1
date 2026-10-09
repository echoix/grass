# Builds the real OSGeo4W setup from a checkout of jef-n/OSGeo4W with the same
# toolchain and flags as src/setup/osgeo4w/package.sh (MSVC 14.44, CMake, Ninja,
# MinSizeRel = /O1 /Ob1, static CRT, bzip2 1.0.8 and zlib sources compiled in).
#
# Variants, all from the same tree:
#   orig  upstream behaviour plus the extraction timing log line (patch 0001)
#   t50   additionally throttle per-file UI updates to every 50 ms (patch 0002)
#   t200  the same with a 200 ms interval
param(
  [Parameter(Mandatory = $true)][string]$Source,
  [Parameter(Mandatory = $true)][string]$Work,
  [string]$Patches = "$PSScriptRoot\patches"
)

$ErrorActionPreference = "Stop"
$ZlibVer = "1.3.2"
$Bzip2Ver = "1.0.8"

function Import-VcVars {
  foreach ($e in "Community", "Professional", "Enterprise", "BuildTools") {
    $dir = "$env:ProgramFiles\Microsoft Visual Studio\2022\$e"
    if (Test-Path "$dir\VC\Auxiliary\Build\vcvars64.bat") { break }
  }
  # Use the toolset the published installer was linked with.
  cmd /c "`"$dir\VC\Auxiliary\Build\vcvars64.bat`" -vcvars_ver=14.44 >nul && set" | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') { Set-Item "env:$($Matches[1])" $Matches[2] }
  }
  cl 2>&1 | Select-String "Version"
  link 2>&1 | Select-String "Version"
}

function Get-Source([string]$url, [string]$fallback, [string]$file, [string]$dir) {
  if (-not (Test-Path "$Work\$dir")) {
    curl.exe -fsSL -o "$Work\$file" $url
    if ($LASTEXITCODE -ne 0 -and $fallback) { curl.exe -fsSL -o "$Work\$file" $fallback }
    if ($LASTEXITCODE -ne 0) { throw "cannot download $file" }
    tar -xzf "$Work\$file" -C $Work
  }
}

New-Item -ItemType Directory -Force $Work | Out-Null
Import-VcVars
# Appended, so that MSVC's link.exe wins over the MSYS one.
$env:PATH += ";C:\msys64\usr\bin"
Get-Source "https://www.zlib.net/zlib-$ZlibVer.tar.gz" "https://github.com/madler/zlib/releases/download/v$ZlibVer/zlib-$ZlibVer.tar.gz" "zlib.tar.gz" "zlib-$ZlibVer"
Get-Source "https://sourceware.org/pub/bzip2/bzip2-$Bzip2Ver.tar.gz" $null "bzip2.tar.gz" "bzip2-$Bzip2Ver"

function Build([string]$name, [string]$define) {
  $cxx = "/O1 /Ob1 /D NDEBUG $define"
  $bdir = "$Work\build-$name"
  cmake -G Ninja -S "$Source\src\setup" -B $bdir `
    -D CMAKE_BUILD_TYPE=MinSizeRel `
    -D CMAKE_EXE_LINKER_FLAGS=/MANIFEST:NO `
    -D "CMAKE_CXX_FLAGS_MINSIZEREL=$cxx" `
    -D ZLIB_SRC="$Work\zlib-$ZlibVer" `
    -D BZIP2_SRC="$Work\bzip2-$Bzip2Ver" `
    -D FLEX_EXECUTABLE=C:/msys64/usr/bin/flex.exe `
    -D BISON_EXECUTABLE=C:/msys64/usr/bin/bison.exe
  if ($LASTEXITCODE -ne 0) { throw "cmake configure failed for $name" }
  cmake --build $bdir
  if ($LASTEXITCODE -ne 0) { throw "build failed for $name" }
  New-Item -ItemType Directory -Force "$Work\setup" | Out-Null
  Copy-Item "$bdir\osgeo4w-setup.exe" "$Work\setup\osgeo4w-setup-$name.exe"
}

Push-Location $Source
try {
  git apply "$Patches\0001-setup-log-extraction-time.diff"
  if ($LASTEXITCODE -ne 0) { throw "patch 0001 failed" }
  Build "orig" ""
  git apply "$Patches\0002-setup-throttle-ui-updates.diff"
  if ($LASTEXITCODE -ne 0) { throw "patch 0002 failed" }
  Build "t50" ""
  Build "t200" "/D UI_UPDATE_INTERVAL_MS=200"
} finally {
  Pop-Location
}
Get-ChildItem "$Work\setup" | ForEach-Object { Write-Host "$($_.Name) $($_.Length) bytes" }
