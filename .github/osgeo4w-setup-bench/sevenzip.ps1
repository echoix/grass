# Measures what the 7-Zip on the runner does with the same real .tar.bz2 packages:
# decoding alone (single and multi-threaded) and decoding plus tar extraction.
param(
  [string]$Work = "C:\bench",
  [int]$Reps = 3,
  [string[]]$Packages = @("python3-notebook", "python3-jupyterlab", "python3-core", "grass-dev", "qgis-ltr-pdb")
)

$ErrorActionPreference = "Stop"
$sz = "C:\Program Files\7-Zip\7z.exe"
Write-Host "## 7-Zip"
& $sz | Select-Object -First 2
Write-Host "Codecs and formats of interest:"
& $sz i | Select-String -Pattern "BZip2|GZip|Zstd|ZSTD|LZMA2|\bTar\b|XZ" | Select-Object -First 12

$dest = "$Work\sz-dest"
$rows = @("| package | 7z decode, 1 thread s | 7z decode, 4 threads s | 7z decode + tar to disk s |", "|---|---|---|---|")

function Best([scriptblock]$block, [bool]$clean) {
  $best = [double]::MaxValue
  for ($i = 0; $i -lt $Reps; $i++) {
    if ($clean -and (Test-Path $dest)) { cmd /c "rd /s /q `"$dest`"" }
    $t = (Measure-Command $block).TotalSeconds
    if ($t -lt $best) { $best = $t }
  }
  if ($clean -and (Test-Path $dest)) { cmd /c "rd /s /q `"$dest`"" }
  $best
}

$Packages | ForEach-Object { Get-ChildItem "$Work\mirror\x86_64\release" -Recurse -Filter "$_-[0-9]*.tar.bz2" } | Sort-Object Length | ForEach-Object {
  $pkg = $_.FullName
  $one = Best { cmd /c "`"$sz`" e `"$pkg`" -so -mmt=1 -bso0 -bsp0 > NUL" } $false
  $four = Best { cmd /c "`"$sz`" e `"$pkg`" -so -mmt=4 -bso0 -bsp0 > NUL" } $false
  $full = Best { cmd /c "`"$sz`" e `"$pkg`" -so -mmt=4 -bso0 -bsp0 | `"$sz`" x -si -ttar -o`"$dest`" -y -bso0 -bsp0" } $true
  $row = "| $($_.Name) | $('{0:N2}' -f $one) | $('{0:N2}' -f $four) | $('{0:N2}' -f $full) |"
  Write-Host $row
  $rows += $row
}
$report = $rows -join "`n"
if ($env:GITHUB_STEP_SUMMARY) { Add-Content $env:GITHUB_STEP_SUMMARY "## 7-Zip on the same packages`n`n$report" }
