# Runs the real setup variants unattended (-q) against a local mirror and reads
# the extraction time the setup itself logs ("Extracted <pkg>: N entries in M ms").
param(
  [string]$Work = "C:\bench",
  [int]$Reps = 5,
  [string[]]$Packages = @("python3-notebook", "python3-jupyterlab", "python3-core", "grass-dev", "qgis-ltr-pdb"),
  [string[]]$Variants = @("orig", "t50", "t200")
)

$ErrorActionPreference = "Stop"
$root = "C:\o4w-bench-root"
$cache = "C:\o4w-bench-cache"
$results = @{}
$failures = 0

# Setup logs its result as soon as extraction is done (patch 0001), so each run
# is stopped at that point: post-install scripts of some packages open modal
# Windows error dialogs when their dependencies are missing, and they are not
# what is measured here.
$timingFile = "$Work\extract-timing.txt"
$env:OSGEO4W_EXTRACT_TIMING_FILE = $timingFile

function Remove-Tree([string]$dir) {
  for ($i = 0; $i -lt 10 -and (Test-Path $dir); $i++) {
    cmd /c "rd /s /q `"$dir`" 2>nul"
    if (Test-Path $dir) { Start-Sleep -Seconds 1 }
  }
}

function Invoke-Setup([string]$variant, [string]$pkg) {
  # Use a fresh local package directory (-l, the download cache) for every run,
  # otherwise setup reuses what an earlier run left in %TEMP%.
  Remove-Tree $root
  Remove-Tree $cache
  Remove-Item $timingFile -ErrorAction SilentlyContinue
  $exe = "$Work\setup\osgeo4w-setup-$variant.exe"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process $exe -PassThru -ArgumentList @(
    "-q", "-s", "http://127.0.0.1:8000/", "-O", "-R", $root, "-l", $cache, "-P", $pkg, "-k", "-n", "-N")
  $line = $null
  while ($sw.Elapsed.TotalSeconds -lt 300) {
    if (Test-Path $timingFile) {
      $line = Select-String -Path $timingFile -Pattern "Extracted $pkg`: (\d+) entries in (\d+) ms" | Select-Object -First 1
      if ($line) { break }
    }
    if ($p.HasExited) { break }
    Start-Sleep -Milliseconds 100
  }
  $total = $sw.Elapsed.TotalSeconds
  if (-not $line) {
    Write-Host "no extraction line for $variant $pkg after $('{0:N0}' -f $total) s (exited: $($p.HasExited)), window title: '$($p.MainWindowTitle)'"
    Get-Process | Where-Object { $_.MainWindowTitle } | ForEach-Object { Write-Host "  window: $($_.ProcessName) '$($_.MainWindowTitle)'" }
    foreach ($d in $cache, $root) {
      Write-Host "  contents of ${d}:"
      Get-ChildItem $d -Force -ErrorAction SilentlyContinue | Select-Object -First 15 | ForEach-Object { Write-Host "    $($_.Name) $($_.Length)" }
    }
  }
  if (-not $p.HasExited) { taskkill /T /F /PID $p.Id | Out-Null }
  if (-not $line) { return $null }
  [pscustomobject]@{ Entries = [int]$line.Matches[0].Groups[1].Value; Ms = [int]$line.Matches[0].Groups[2].Value; Total = $total }
}

Write-Host "## Environment"
Get-CimInstance Win32_Processor | ForEach-Object { Write-Host "$($_.Name), $($_.NumberOfLogicalProcessors) logical CPUs" }
try { Write-Host "Defender real-time protection enabled: $(-not (Get-MpPreference).DisableRealtimeMonitoring)" } catch { }

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
        if ($failures -ge 2) { throw "setup failed twice in a row, giving up" }
      }
      if ($r) {
        $failures = 0
        Write-Host "[$(Get-Date -Format HH:mm:ss)] rep $rep $pkg $variant entries=$($r.Entries) extract_ms=$($r.Ms) wall_s=$('{0:N1}' -f $r.Total)"
        $k = "$pkg|$variant"
        if (-not $results[$k]) { $results[$k] = @() }
        $results[$k] += $r
      }
    }
  }
}
Remove-Tree $root
Remove-Tree $cache

function Get-Median($v) { $s = $v | Sort-Object; $s[[math]::Floor($s.Count / 2)] }
$rows = @("| package | entries | variant | extraction min ms | extraction median ms | vs orig (median) | until extraction logged, median s |", "|---|---|---|---|---|---|---|")
foreach ($pkg in $Packages) {
  $base = $null
  foreach ($variant in $Variants) {
    $r = $results["$pkg|$variant"]
    if (-not $r) { continue }
    $ms = $r | ForEach-Object { $_.Ms }
    $med = Get-Median $ms
    if ($variant -eq $Variants[0]) { $base = $med }
    $delta = if ($base) { '{0:+0.0;-0.0}%' -f (100.0 * ($med - $base) / $base) } else { "" }
    $rows += "| $pkg | $($r[0].Entries) | $variant | $(($ms | Measure-Object -Minimum).Minimum) | $med | $delta | $('{0:N1}' -f (Get-Median ($r | ForEach-Object { $_.Total }))) |"
  }
}
$report = $rows -join "`n"
Write-Host $report
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Real setup.exe: extraction time per variant`n`n$report" }
