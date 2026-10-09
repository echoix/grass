# Parity of the rebased setup with the fork, before any speed is reported.
#
# Installs python3-core and python3-notebook completely (post-install scripts
# included, nothing is killed) with the fork (F0) and the rebased build in plain
# (R2) and Cygwin (R0) file semantics, each into its own root, and compares:
#   - the packages setup extracted against the closure computed from setup.ini,
#   - the installed.db and the <package>.lst.gz manifests,
#   - every file below the root: size, SHA-256, last write time,
#   - setup's exit code and the post-install scripts that ran,
#   - whether files got explicit (non-inherited) ACL entries.
# The variants that pass go to $Work\parity-ok.txt for the benchmark.
param(
  [string]$Work = "C:\bench",
  [string[]]$Targets = @("python3-core", "python3-notebook"),
  [string[]]$Variants = @("F0", "R2", "R0")
)

$ErrorActionPreference = "Stop"
$out = "$Work\parity"
New-Item -ItemType Directory -Force $out | Out-Null
$closures = Get-Content "$Work\mirror\closures.json" -Raw | ConvertFrom-Json -AsHashtable
$report = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { Write-Host $s; $report.Add($s) }

$specs = @{
  F0 = @{ exe = "osgeo4w-setup-orig.exe"; env = @{} }
  R2 = @{ exe = "rb-timing.exe"; env = @{} }
  R0 = @{ exe = "rb-timing.exe"; env = @{ OSGEO4W_SETUP_FILE_SEMANTICS = "cygwin" } }
}

function Remove-Tree([string]$dir) {
  for ($i = 0; $i -lt 10 -and (Test-Path $dir); $i++) {
    cmd /c "rd /s /q `"$dir`" 2>nul"
    if (Test-Path $dir) { Start-Sleep -Seconds 1 }
  }
}

# Runs setup to its end.  Returns exit code, seconds, and whether it had to be killed.
function Invoke-Full([string]$variant, [string]$root, [string[]]$extra, [string]$tag, [int]$timeoutSec = 1200, [string]$site = "http://127.0.0.1:8000/") {
  $cache = "$Work\parity-cache-$tag"
  Remove-Tree $cache
  $timing = "$out\timing-$tag.txt"
  Remove-Item $timing -ErrorAction SilentlyContinue
  $env:OSGEO4W_EXTRACT_TIMING_FILE = $timing
  foreach ($k in $specs[$variant].env.Keys) { Set-Item "env:$k" $specs[$variant].env[$k] }
  $args = @("-q", "-s", $site, "-O", "-R", $root, "-l", $cache, "-k", "-n", "-N") + $extra
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process "$Work\setup\$($specs[$variant].exe)" -PassThru -ArgumentList $args
  foreach ($k in $specs[$variant].env.Keys) { Remove-Item "env:$k" }
  Remove-Item env:OSGEO4W_EXTRACT_TIMING_FILE
  $killed = $false
  if (-not $p.WaitForExit($timeoutSec * 1000)) {
    $killed = $true
    Say "  $tag: setup still running after $timeoutSec s, window title '$($p.MainWindowTitle)'; killing"
    Get-Process | Where-Object { $_.MainWindowTitle } | ForEach-Object { Say "    window: $($_.ProcessName) '$($_.MainWindowTitle)'" }
    taskkill /T /F /PID $p.Id | Out-Null
  }
  foreach ($log in "var\log\setup.log", "var\log\setup.log.full") {
    if (Test-Path "$root\$log") { Copy-Item "$root\$log" "$out\$tag-$(Split-Path $log -Leaf)" -Force }
  }
  [pscustomobject]@{ Exit = $(if ($killed) { -1 } else { $p.ExitCode }); Seconds = $sw.Elapsed.TotalSeconds; Killed = $killed; Timing = $timing }
}

function Get-Extracted([string]$timing) {
  if (-not (Test-Path $timing)) { return @() }
  @(Select-String -Path $timing -Pattern "^Extracted (\S+): (\d+) entries" | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
}

function Get-InstalledDb([string]$root) {
  $f = "$root\etc\setup\installed.db"
  if (-not (Test-Path $f)) { return @() }
  @(Get-Content $f | Select-Object -Skip 1 | ForEach-Object { ($_ -split " ")[1] } | Sort-Object)
}

# every file below the root with what is compared
function Get-Tree([string]$root) {
  $rootLen = $root.Length + 1
  Get-ChildItem $root -Recurse -Force -File -ErrorAction SilentlyContinue | ForEach-Object {
    $rel = $_.FullName.Substring($rootLen)
    if ($rel -like "var\log\*" -or $rel -like "var\run\*") { return }
    [pscustomobject]@{
      Path = $rel.ToLowerInvariant()
      Size = $_.Length
      Hash = if ($rel -like "etc\setup\*.lst.gz") { "(see manifests)" } else { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
      Mtime = $_.LastWriteTimeUtc.Ticks
    }
  }
}

# decompressed manifest lines of etc\setup\*.lst.gz
function Get-Manifests([string]$root) {
  $m = @{}
  foreach ($f in Get-ChildItem "$root\etc\setup\*.lst.gz" -ErrorAction SilentlyContinue) {
    $fs = [IO.File]::OpenRead($f.FullName)
    $gz = New-Object IO.Compression.GZipStream($fs, [IO.Compression.CompressionMode]::Decompress)
    $sr = New-Object IO.StreamReader($gz)
    $m[$f.Name] = $sr.ReadToEnd()
    $sr.Dispose(); $fs.Dispose()
  }
  $m
}

function Compare-Roots([string]$a, [string]$b, [string]$nameA, [string]$nameB, [string]$tag) {
  $ta = @{}; Get-Tree $a | ForEach-Object { $ta[$_.Path] = $_ }
  $tb = @{}; Get-Tree $b | ForEach-Object { $tb[$_.Path] = $_ }
  $onlyA = @($ta.Keys | Where-Object { -not $tb.ContainsKey($_) } | Sort-Object)
  $onlyB = @($tb.Keys | Where-Object { -not $ta.ContainsKey($_) } | Sort-Object)
  $hash = @(); $size = @(); $mtime = @()
  foreach ($k in $ta.Keys) {
    if (-not $tb.ContainsKey($k)) { continue }
    if ($ta[$k].Size -ne $tb[$k].Size) { $size += $k }
    elseif ($ta[$k].Hash -ne $tb[$k].Hash) { $hash += $k }
    if ([math]::Abs($ta[$k].Mtime - $tb[$k].Mtime) -gt 20000000) { $mtime += $k }   # 2 s
  }
  $ma = Get-Manifests $a; $mb = Get-Manifests $b
  $mdiff = @($ma.Keys + $mb.Keys | Sort-Object -Unique | Where-Object { $ma[$_] -ne $mb[$_] })
  $dba = Get-InstalledDb $a; $dbb = Get-InstalledDb $b
  $dbdiff = Compare-Object $dba $dbb
  $ok = ($onlyA.Count + $onlyB.Count + $hash.Count + $size.Count + $mdiff.Count + @($dbdiff).Count) -eq 0
  Say "  $tag $nameA vs ${nameB}: files $($ta.Count) / $($tb.Count); only in ${nameA}: $($onlyA.Count); only in ${nameB}: $($onlyB.Count); size differs: $($size.Count); content differs: $($hash.Count); mtime differs by > 2 s: $($mtime.Count); manifests differing: $($mdiff.Count); installed.db differences: $(@($dbdiff).Count) => $(if ($ok) { 'IDENTICAL' } else { 'DIFFERENT' })"
  $detail = @("## $tag $nameA vs $nameB")
  foreach ($l in @(@("only in $nameA", $onlyA), @("only in $nameB", $onlyB), @("size differs", $size), @("content differs", $hash), @("mtime differs", $mtime), @("manifest differs", $mdiff))) {
    $detail += "### $($l[0]) ($(@($l[1]).Count))"
    $detail += @($l[1] | Select-Object -First 200)
  }
  $detail += "### installed.db"
  $detail += @($dbdiff | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" })
  $detail | Set-Content "$out\diff-$tag-$nameA-$nameB.txt"
  $ok
}

# explicit (non-inherited) ACEs on a sample of files and directories
function Get-AclSummary([string]$root) {
  $files = @(Get-ChildItem $root -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\var\log\*" } | Select-Object -First 300)
  $dirs = @(Get-ChildItem $root -Recurse -Force -Directory -ErrorAction SilentlyContinue | Select-Object -First 100)
  $explicit = 0
  foreach ($i in $files + $dirs) {
    try { if (@((Get-Acl $i.FullName).Access | Where-Object { -not $_.IsInherited }).Count -gt 0) { $explicit++ } } catch { }
  }
  "$explicit of $($files.Count + $dirs.Count) sampled items have explicit ACL entries"
}

$passed = @{}
foreach ($v in $Variants) { $passed[$v] = $true }
$roots = @{}

Say "# Parity: closure, files, manifests, exit status"
foreach ($t in $Targets) {
  Say ""
  Say "## Target $t ($($closures[$t].Count) packages in the closure computed from setup.ini)"
  foreach ($v in $Variants) {
    $root = "C:\parity-root-$v-$t"
    Remove-Tree $root
    $roots["$v|$t"] = $root
    $r = Invoke-Full $v $root @("-P", $t) "$v-$t"
    $ext = Get-Extracted $r.Timing
    $missing = @($closures[$t] | Where-Object { $ext -notcontains $_ })
    $extra = @($ext | Where-Object { $closures[$t] -notcontains $_ })
    $dbpk = @(Get-InstalledDb $root | ForEach-Object { $_ -replace "-[0-9][^-]*(-[0-9]+)?\.tar\.bz2$", "" } | Sort-Object)
    $dbMissing = @($closures[$t] | Where-Object { $dbpk -notcontains $_ })
    Say "  $v ${t}: exit $($r.Exit), $([math]::Round($r.Seconds)) s$(if ($r.Killed) { ', KILLED (did not finish)' }); extracted $($ext.Count); not extracted: $($missing -join ' '); extra: $($extra -join ' '); in installed.db: $($dbpk.Count), closure packages missing there: $($dbMissing -join ' ')"
    $scriptsDone = @(Get-ChildItem "$root\etc\postinstall\*.done" -ErrorAction SilentlyContinue).Count
    $scriptsLeft = @(Get-ChildItem "$root\etc\postinstall" -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -ne ".done" }).Count
    Say "  $v ${t}: post-install scripts done: $scriptsDone, left behind: $scriptsLeft; $(Get-AclSummary $root)"
    if ($r.Exit -ne 0 -or $r.Killed -or $missing.Count -or $extra.Count -or $dbMissing.Count) { $passed[$v] = $false }
  }
  $base = $Variants[0]
  foreach ($v in $Variants | Select-Object -Skip 1) {
    if (-not (Compare-Roots $roots["$base|$t"] $roots["$v|$t"] $base $v $t)) {
      # R0 (Cygwin semantics) may differ in ACLs only; any file difference fails a variant
      $passed[$v] = $false
    }
  }
}

$ok = @($Variants | Where-Object { $passed[$_] })
Say ""
Say "Variants that passed parity with $($Variants[0]): $($ok -join ', ')"
$ok | Set-Content "$Work\parity-ok.txt"
$report | Set-Content "$out\parity-report.md"
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Parity`n`n``````n$($report -join "`n")`n``````" }
