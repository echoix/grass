# Measures what 7-Zip (the version on the runner) does with the real .tar.bz2
# packages, for the same dependency closures that run_setup.ps1 installs:
#   - decode only, summed over all packages of a closure, with 1 and 4 threads
#   - the same with stock bzip2 1.0.8 (Git for Windows' bzip2.exe, single thread)
#   - for the target package alone: decode + tar extraction to disk through a pipe
# All archives of a closure go to one 7z.exe process so that process start-up is
# not counted per package. bzip2.exe is run once per package from a batch file.
param(
  [string]$Work = "C:\bench",
  [int]$Reps = 2,
  [string[]]$Packages = @("python3-notebook", "python3-jupyterlab", "python3-core", "grass-dev", "qgis-ltr-pdb")
)

$ErrorActionPreference = "Stop"
$sz = "C:\Program Files\7-Zip\7z.exe"
$bz = "C:\Program Files\Git\usr\bin\bzip2.exe"
Write-Host "## 7-Zip"
& $sz | Select-Object -First 2
Write-Host "Codecs and formats of interest:"
& $sz i | Select-String -Pattern "BZip2|GZip|Zstd|ZSTD|LZMA2|\bTar\b|XZ" | Select-Object -First 12
Get-CimInstance Win32_Processor | ForEach-Object { Write-Host "$($_.Name), $($_.NumberOfLogicalProcessors) logical CPUs" }

$closures = Get-Content "$Work\mirror\closures.json" -Raw | ConvertFrom-Json -AsHashtable
$paths = @{}
$current = $null
foreach ($l in [IO.File]::ReadLines("$Work\mirror\x86_64\setup.ini")) {
  if ($l.StartsWith("@ ")) { $current = $l.Substring(2).Trim() }
  elseif ($l.StartsWith("install:") -and $current -and -not $paths.ContainsKey($current)) {
    $paths[$current] = "$Work\mirror\" + ($l.Split(" ")[1] -replace "/", "\")
  }
}

function Best([scriptblock]$block) {
  $best = [double]::MaxValue
  for ($i = 0; $i -lt $Reps; $i++) {
    $t = (Measure-Command $block).TotalSeconds
    if ($t -lt $best) { $best = $t }
  }
  $best
}

# Runs one 7z.exe decoding all archives to stdout and discards the output. The
# output is read here, so nothing is written to disk. Fails loudly: an earlier
# version silently measured 0 s because 7z.exe had exited with an error.
function Invoke-7zDecode([string[]]$archives, [int]$threads) {
  $psi = [Diagnostics.ProcessStartInfo]::new($sz)
  foreach ($a in @("e") + $archives + @("-so", "-mmt=$threads")) { $psi.ArgumentList.Add($a) }
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = [Diagnostics.Process]::Start($psi)
  $err = $p.StandardError.ReadToEndAsync()
  $bytes = 0L
  $buf = New-Object byte[] 1048576
  $stream = $p.StandardOutput.BaseStream
  while (($n = $stream.Read($buf, 0, $buf.Length)) -gt 0) { $bytes += $n }
  $p.WaitForExit()
  if ($p.ExitCode -ne 0 -or $bytes -lt 1MB) {
    throw "7z.exe exit code $($p.ExitCode), $bytes bytes of output: $($err.Result)"
  }
}

$rows = @("| target | packages in closure | compressed MB | 7-Zip decode, 1 thread s | 7-Zip decode, 4 threads s | stock bzip2 1.0.8 decode s |", "|---|---|---|---|---|---|")
foreach ($pkg in $Packages) {
  $archives = @($closures[$pkg] | ForEach-Object { $paths[$_] } | Where-Object { $_ })
  $mb = ($archives | ForEach-Object { (Get-Item $_).Length } | Measure-Object -Sum).Sum / 1MB
  $one = Best { Invoke-7zDecode $archives 1 }
  $four = Best { Invoke-7zDecode $archives 4 }
  $bat = "$Work\bzip2-all.cmd"
  $archives | ForEach-Object { "`"$bz`" -dc `"$_`" > NUL" } | Set-Content $bat -Encoding ascii
  $stock = Best { cmd /c $bat }
  $row = "| $pkg | $($archives.Count) | $('{0:N0}' -f $mb) | $('{0:N1}' -f $one) | $('{0:N1}' -f $four) | $('{0:N1}' -f $stock) |"
  Write-Host $row
  $rows += $row
}
$report = $rows -join "`n"
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Decoding whole dependency closures`n`n$report" }

# Target package alone: decode plus tar extraction to disk through a pipe.
$dest = "$Work\sz-dest"
$rows = @("| package | 7z decode+tar to disk, 4 threads s |", "|---|---|")
foreach ($pkg in $Packages) {
  $file = $paths[$pkg]
  $t = Best {
    if (Test-Path $dest) { cmd /c "rd /s /q `"$dest`"" }
    cmd /c "`"$sz`" e `"$file`" -so -mmt=4 -bso0 -bsp0 | `"$sz`" x -si -ttar -o`"$dest`" -y -bso0 -bsp0"
  }
  if (Test-Path $dest) { cmd /c "rd /s /q `"$dest`"" }
  $row = "| $pkg | $('{0:N1}' -f $t) |"
  Write-Host $row
  $rows += $row
}
$report = $rows -join "`n"
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## Target package alone, decode and extract to disk`n`n$report" }
