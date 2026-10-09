# Runs the real setup variants unattended (-q) against a local mirror and reads
# the extraction time the setup itself logs ("Extracted <pkg>: N entries in M ms").
#
# Variants (all in one job, rotated order per repetition):
#   F0   fork (jef-n/OSGeo4W src/setup), MSVC 14.44, as published plus the timing line
#   F1   F0 with UI updates throttled to every 50 ms
#   F0m  F0 built with the mingw-w64 toolchain used for the rebased builds
#   R0   OSGeo4W adaptations on current Cygwin setup, Cygwin file semantics (NT ACLs
#        on every file, second pass over each package for symlinks)
#   R1   R0 with the 50 ms UI throttle
#   R2   R0 with plain file semantics and no second pass (OSGEO4W_SETUP_FILE_SEMANTICS unset)
#   R3   R2 with the 50 ms UI throttle
#   R2s  R0 with only the second pass skipped
param(
  [string]$Work = "C:\bench",
  [int]$Reps = 3,
  [string[]]$Packages = @("python3-notebook", "python3-jupyterlab", "python3-core", "grass-dev", "qgis-ltr-pdb"),
  [string[]]$Variants = @("F0", "F1", "F0m", "R0", "R1", "R2", "R3", "R2s")
)

$ErrorActionPreference = "Stop"
$root = "C:\o4w-bench-root"
$cache = "C:\o4w-bench-cache"
$results = @{}
$closures = Get-Content "$Work\mirror\closures.json" -Raw | ConvertFrom-Json -AsHashtable
$failures = 0
$resultsFile = "$Work\results.jsonl"
Remove-Item $resultsFile -ErrorAction SilentlyContinue

$specs = @{
  F0  = @{ exe = "osgeo4w-setup-orig.exe"; env = @{} }
  F1  = @{ exe = "osgeo4w-setup-t50.exe"; env = @{} }
  F0m = @{ exe = "fork-mingw.exe"; env = @{} }
  R0  = @{ exe = "rb-timing.exe"; env = @{ OSGEO4W_SETUP_FILE_SEMANTICS = "cygwin" } }
  R1  = @{ exe = "rb-throttle.exe"; env = @{ OSGEO4W_SETUP_FILE_SEMANTICS = "cygwin" } }
  R2  = @{ exe = "rb-timing.exe"; env = @{} }
  R3  = @{ exe = "rb-throttle.exe"; env = @{} }
  R2s = @{ exe = "rb-timing.exe"; env = @{ OSGEO4W_SETUP_FILE_SEMANTICS = "cygwin"; OSGEO4W_SETUP_SKIP_SYMLINK_PASS = "1" } }
}
$Variants = $Variants | Where-Object { Test-Path "$Work\setup\$($specs[$_].exe)" }
Write-Host "variants available: $($Variants -join ', ')"

# Setup logs its result as soon as extraction is done, so each run is stopped at
# that point: post-install scripts of some packages open modal Windows error
# dialogs when their dependencies are missing, and they are not what is measured.
$timingFile = "$Work\extract-timing.txt"
$env:OSGEO4W_EXTRACT_TIMING_FILE = $timingFile

function Remove-Tree([string]$dir) {
  for ($i = 0; $i -lt 10 -and (Test-Path $dir); $i++) {
    cmd /c "rd /s /q `"$dir`" 2>nul"
    if (Test-Path $dir) { Start-Sleep -Seconds 1 }
  }
}

function Invoke-Setup([string]$variant, [string]$pkg) {
  $expected = $closures[$pkg].Count
  # Use a fresh local package directory (-l, the download cache) for every run,
  # otherwise setup reuses what an earlier run left in %TEMP%.
  Remove-Tree $root
  Remove-Tree $cache
  Remove-Item $timingFile -ErrorAction SilentlyContinue
  $exe = "$Work\setup\$($specs[$variant].exe)"
  foreach ($k in $specs[$variant].env.Keys) { Set-Item "env:$k" $specs[$variant].env[$k] }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process $exe -PassThru -ArgumentList @(
    "-q", "-s", "http://127.0.0.1:8000/", "-O", "-R", $root, "-l", $cache, "-P", $pkg, "-k", "-n", "-N")
  foreach ($k in $specs[$variant].env.Keys) { Remove-Item "env:$k" }
  $lines = @()
  while ($sw.Elapsed.TotalSeconds -lt 900) {
    if (Test-Path $timingFile) {
      $lines = @(Select-String -Path $timingFile -Pattern "^Extracted (\S+): (\d+) entries in (\d+) ms")
      if ($lines.Count -ge $expected) { break }
    }
    if ($p.HasExited) { break }
    Start-Sleep -Milliseconds 200
  }
  $total = $sw.Elapsed.TotalSeconds
  if ($lines.Count -lt $expected) {
    Write-Host "only $($lines.Count) of $expected packages extracted for $variant $pkg after $('{0:N0}' -f $total) s (exited: $($p.HasExited)), window title: '$($p.MainWindowTitle)'"
    Get-Process | Where-Object { $_.MainWindowTitle } | ForEach-Object { Write-Host "  window: $($_.ProcessName) '$($_.MainWindowTitle)'" }
    foreach ($d in $cache, $root) {
      Write-Host "  contents of ${d}:"
      Get-ChildItem $d -Force -ErrorAction SilentlyContinue | Select-Object -First 15 | ForEach-Object { Write-Host "    $($_.Name) $($_.Length)" }
    }
    foreach ($log in "$root\var\log\setup.log", "$root\var\log\setup.log.full") {
      if (Test-Path $log) { Write-Host "  tail of ${log}:"; Get-Content $log -Tail 25 | ForEach-Object { Write-Host "    $_" } }
    }
  }
  if (-not $p.HasExited) { taskkill /T /F /PID $p.Id | Out-Null }
  if ($lines.Count -lt $expected) { return $null }
  $all = $lines | ForEach-Object { [pscustomobject]@{ Name = $_.Matches[0].Groups[1].Value; Entries = [int]$_.Matches[0].Groups[2].Value; Ms = [int]$_.Matches[0].Groups[3].Value } }
  $self = $all | Where-Object { $_.Name -eq $pkg } | Select-Object -First 1
  [pscustomobject]@{
    Packages = $all.Count
    Entries = ($all | Measure-Object Entries -Sum).Sum
    Ms = ($all | Measure-Object Ms -Sum).Sum
    SelfEntries = $self.Entries
    SelfMs = $self.Ms
    Total = $total
    PerPackage = $all
  }
}

Write-Host "## Environment"
Get-CimInstance Win32_Processor | ForEach-Object { Write-Host "$($_.Name), $($_.NumberOfLogicalProcessors) logical CPUs" }
try { Write-Host "Defender real-time protection enabled: $(-not (Get-MpPreference).DisableRealtimeMonitoring)" } catch { Write-Host "Defender state unknown: $_" }

# Interleave the variants in each repetition to spread out drift on the runner.
for ($rep = 1; $rep -le $Reps; $rep++) {
  foreach ($pkg in $Packages) {
    # Rotate the order so that no variant is always first (first runs are slower).
    $n = $Variants.Count
    $order = 0..($n - 1) | ForEach-Object { $Variants[($_ + $rep - 1) % $n] }
    foreach ($variant in $order) {
      $r = Invoke-Setup $variant $pkg
      if (-not $r) {
        # Fail fast if the unattended setup does not work at all, instead of
        # waiting for every remaining run to time out.
        $failures++
        if ($failures -ge 3) { throw "setup failed three times in a row, giving up" }
      }
      if ($r) {
        $failures = 0
        Write-Host "[$(Get-Date -Format HH:mm:ss)] rep $rep $pkg $variant packages=$($r.Packages) entries=$($r.Entries) all_extract_ms=$($r.Ms) target_entries=$($r.SelfEntries) target_extract_ms=$($r.SelfMs) wall_s=$('{0:N1}' -f $r.Total)"
        $k = "$pkg|$variant"
        if (-not $results[$k]) { $results[$k] = @() }
        $results[$k] += $r
        (@{ rep = $rep; pkg = $pkg; variant = $variant; packages = $r.Packages; entries = $r.Entries; ms = $r.Ms; self_entries = $r.SelfEntries; self_ms = $r.SelfMs; wall_s = $r.Total; per_package = $r.PerPackage } | ConvertTo-Json -Compress -Depth 4) | Add-Content $resultsFile
      }
    }
  }
}
Remove-Tree $root
Remove-Tree $cache

function Get-Median($v) { $s = $v | Sort-Object; $s[[math]::Floor($s.Count / 2)] }
$rows = @("| target package | packages | entries | variant | runs | whole install: min ms | median ms | vs F0 | entries/s (median) | target package only: median ms | vs F0 | start to last package: median s | vs F0 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|")
foreach ($pkg in $Packages) {
  $baseAll = $null; $baseSelf = $null; $baseWall = $null
  foreach ($variant in $Variants) {
    $r = $results["$pkg|$variant"]
    if (-not $r) { continue }
    $all = $r | ForEach-Object { $_.Ms }
    $self = $r | ForEach-Object { $_.SelfMs }
    $wall = $r | ForEach-Object { $_.Total }
    $medAll = Get-Median $all
    $medSelf = Get-Median $self
    $medWall = Get-Median $wall
    if ($variant -eq "F0") { $baseAll = $medAll; $baseSelf = $medSelf; $baseWall = $medWall }
    $dAll = if ($baseAll) { '{0:+0.0;-0.0}%' -f (100.0 * ($medAll - $baseAll) / $baseAll) } else { "" }
    $dSelf = if ($baseSelf) { '{0:+0.0;-0.0}%' -f (100.0 * ($medSelf - $baseSelf) / $baseSelf) } else { "" }
    $dWall = if ($baseWall) { '{0:+0.0;-0.0}%' -f (100.0 * ($medWall - $baseWall) / $baseWall) } else { "" }
    $eps = '{0:N0}' -f ($r[0].Entries / ($medAll / 1000.0))
    $rows += "| $pkg | $($r[0].Packages) | $($r[0].Entries) | $variant | $($r.Count) | $(($all | Measure-Object -Minimum).Minimum) | $medAll | $dAll | $eps | $medSelf | $dSelf | $('{0:N1}' -f $medWall) | $dWall |"
  }
}
$report = $rows -join "`n"
Write-Host $report
$report | Set-Content "$Work\report.md"
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Real setup.exe: extraction time per variant`n`n$report" }
