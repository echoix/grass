# Runs the real setup variants unattended (-q) against a local mirror and reads
# the extraction time the setup itself logs ("Extracted <pkg>: N entries in M ms").
param(
  [string]$Work = "C:\bench",
  [int]$Reps = 3,
  [string[]]$Packages = @("python3-notebook", "python3-core", "grass-dev", "qgis-ltr-pdb"),
  [string[]]$Variants = @("orig", "t50", "buf", "t50buf")
)

$ErrorActionPreference = "Stop"
$root = "C:\o4w-bench-root"
$cache = "C:\o4w-bench-cache"
$results = @{}
$closures = Get-Content "$Work\mirror\closures.json" -Raw | ConvertFrom-Json -AsHashtable
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
  $expected = $closures[$pkg].Count
  # Use a fresh local package directory (-l, the download cache) for every run,
  # otherwise setup reuses what an earlier run left in %TEMP%.
  Remove-Tree $root
  Remove-Tree $cache
  Remove-Item $timingFile -ErrorAction SilentlyContinue
  $exe = "$Work\setup\osgeo4w-setup-$variant.exe"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process $exe -PassThru -ArgumentList @(
    "-q", "-s", "http://127.0.0.1:8000/", "-O", "-R", $root, "-l", $cache, "-P", $pkg, "-k", "-n", "-N")
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
  }
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
        Write-Host "[$(Get-Date -Format HH:mm:ss)] rep $rep $pkg $variant packages=$($r.Packages) entries=$($r.Entries) all_extract_ms=$($r.Ms) target_entries=$($r.SelfEntries) target_extract_ms=$($r.SelfMs) wall_s=$('{0:N1}' -f $r.Total)"
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
$rows = @("| target package | packages | entries | variant | whole install: min ms | median ms | vs orig | target package only: median ms | vs orig | wall s median | vs orig |", "|---|---|---|---|---|---|---|---|---|---|---|")
foreach ($pkg in $Packages) {
  $baseAll = $null
  $baseSelf = $null
  $baseWall = $null
  foreach ($variant in $Variants) {
    $r = $results["$pkg|$variant"]
    if (-not $r) { continue }
    $all = $r | ForEach-Object { $_.Ms }
    $self = $r | ForEach-Object { $_.SelfMs }
    $medAll = Get-Median $all
    $medSelf = Get-Median $self
    $medWall = Get-Median ($r | ForEach-Object { $_.Total })
    if ($variant -eq $Variants[0]) { $baseAll = $medAll; $baseSelf = $medSelf; $baseWall = $medWall }
    $dWall = if ($baseWall) { '{0:+0.0;-0.0}%' -f (100.0 * ($medWall - $baseWall) / $baseWall) } else { "" }
    $dAll = if ($baseAll) { '{0:+0.0;-0.0}%' -f (100.0 * ($medAll - $baseAll) / $baseAll) } else { "" }
    $dSelf = if ($baseSelf) { '{0:+0.0;-0.0}%' -f (100.0 * ($medSelf - $baseSelf) / $baseSelf) } else { "" }
    $rows += "| $pkg | $($r[0].Packages) | $($r[0].Entries) | $variant | $(($all | Measure-Object -Minimum).Minimum) | $medAll | $dAll | $medSelf | $dSelf | $('{0:N1}' -f $medWall) | $dWall |"
  }
}
$report = $rows -join "`n"
Write-Host $report
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Real setup.exe: extraction time per variant`n`n$report" }
