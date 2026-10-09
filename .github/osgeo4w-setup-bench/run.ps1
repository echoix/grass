param([string]$Work = "C:\bench", [Parameter(Mandatory = $true)][string]$Package)

$ErrorActionPreference = "Stop"
$pkgs = Get-ChildItem "$Work\pkgs\$Package-[0-9]*.tar.bz2"
$dest = "$Work\dest"
$rows = @()

function Get-Defender {
  try { return -not (Get-MpPreference).DisableRealtimeMonitoring } catch { return "unknown" }
}

function Set-Defender([bool]$on) {
  try {
    Set-MpPreference -DisableRealtimeMonitoring (-not $on)
  } catch {
    Write-Host "Could not change Defender state: $_"
  }
  Write-Host "Defender real-time protection enabled: $(Get-Defender)"
}

# cmd's rd is far faster than Remove-Item on trees with many files.
function Remove-Dest {
  if (Test-Path $dest) { cmd /c "rd /s /q `"$dest`"" }
}

function Invoke-Bench([string]$exe, [string[]]$benchArgs, [bool]$extract) {
  $secs = @()
  $info = ""
  for ($i = 0; $i -lt $reps; $i++) {
    if ($extract) { Remove-Dest }
    $out = & $exe @benchArgs
    if ($LASTEXITCODE -ne 0) { throw "$exe failed: $out" }
    $line = $out | Where-Object { $_ -like "RESULT*" } | Select-Object -First 1
    $secs += [double]($line -replace '.*secs=', '')
    $info = $line
    Write-Host "[$(Get-Date -Format HH:mm:ss)] rep $($i + 1)/$reps $line"
  }
  if ($extract) { Remove-Dest }
  $sorted = $secs | Sort-Object
  return [pscustomobject]@{ Min = $sorted[0]; Median = $sorted[[int][math]::Floor($sorted.Count / 2)]; Info = $info }
}

function Add-Row($pkg, $defender, $label, $r) {
  $files = if ($r.Info -match 'files=(\d+)') { $Matches[1] } else { "" }
  $mb = if ($r.Info -match 'bytes=(\d+)') { '{0:N0}' -f ([double]$Matches[1] / 1MB) } else { "" }
  $script:rows += "| $($pkg.Name) | $defender | $label | $files | $mb | $('{0:N2}' -f $r.Min) | $('{0:N2}' -f $r.Median) |"
  Write-Host $script:rows[-1]
}

$extractCases = @(
  @{ Label = "baseline (O1; in=4K copy=16K ui=on)"; Exe = "O1"; Args = @("--in", "4096", "--copy", "16384", "--ui", "1") },
  @{ Label = "baseline built /O2"; Exe = "O2"; Args = @("--in", "4096", "--copy", "16384", "--ui", "1") },
  @{ Label = "no per-file UI messages"; Exe = "O1"; Args = @("--in", "4096", "--copy", "16384", "--ui", "0") },
  @{ Label = "copy chunk 64K"; Exe = "O1"; Args = @("--in", "4096", "--copy", "65536", "--ui", "1") },
  @{ Label = "bz2 input reads 64K"; Exe = "O1"; Args = @("--in", "65536", "--copy", "16384", "--ui", "1") },
  @{ Label = "64K reads + 64K copy + no UI (O1)"; Exe = "O1"; Args = @("--in", "65536", "--copy", "65536", "--ui", "0") },
  @{ Label = "64K reads + 64K copy + no UI (O2)"; Exe = "O2"; Args = @("--in", "65536", "--copy", "65536", "--ui", "0") }
)

Write-Host "## Environment"
Get-CimInstance Win32_OperatingSystem | ForEach-Object { Write-Host "$($_.Caption) $($_.Version)" }
Get-CimInstance Win32_Processor | ForEach-Object { Write-Host "$($_.Name), $($_.NumberOfLogicalProcessors) logical CPUs" }
Get-Volume -DriveLetter C | ForEach-Object { Write-Host "C: $($_.FileSystemType) $([math]::Round($_.Size / 1GB)) GB" }
Write-Host "Defender real-time protection enabled at start: $(Get-Defender)"

$defenderStart = Get-Defender
$states = @($defenderStart)
if ($defenderStart -eq $true) { $states += $false }

foreach ($state in $states) {
  if ($state -ne $defenderStart) { Set-Defender $state }
  $defLabel = if ($state -eq $true) { "on" } elseif ($state -eq $false) { "off" } else { "unknown" }

  foreach ($pkg in $pkgs) {
    # Fewer repetitions for big packages to keep the whole job bounded.
    $reps = if ($pkg.Length -gt 30MB) { 2 } else { 3 }
    Write-Host "=== $($pkg.Name) ($([math]::Round($pkg.Length / 1MB)) MB, $reps reps, Defender $defLabel)"
    foreach ($exe in @("O1", "O2")) {
      $r = Invoke-Bench "$Work\bench_$exe.exe" @("decomp", $pkg.FullName, "--in", "4096") $false
      Add-Row $pkg $defLabel "decompress only, 4K reads, built /$exe" $r
    }
    foreach ($case in $extractCases) {
      # Only the baseline and the combined cases are repeated with Defender
      # off, and for the few-huge-files control package.
      $short = $state -eq $false -or $pkg.Name -like "*-pdb-*"
      if ($short -and $case.Label -notmatch "baseline|64K reads \+ 64K") { continue }
      $a = @("extract", $pkg.FullName, $dest) + $case.Args
      $r = Invoke-Bench "$Work\bench_$($case.Exe).exe" $a $true
      Add-Row $pkg $defLabel "extract: $($case.Label)" $r
    }
  }
}
if ($states.Count -gt 1) { Set-Defender $defenderStart }

$header = @("| package | Defender | case | files | MB out | min s | median s |", "|---|---|---|---|---|---|---|")
$report = ($header + $rows) -join "`n"
Write-Host $report
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Extraction timings: $Package`n`n$report" }
