"Setup OSGeo4W environment action"
"::group::Download OSGeo4W installer"
$exe = 'osgeo4w-setup.exe'
$url = $env:INPUT_SITE + $exe
$setup = '.\' + $exe
echo "Starting download of $url..."
Invoke-WebRequest $url -OutFile $setup
echo "Download completed"
"::endgroup::"

$args_ = @(
    '--advanced'     # Advanced install (default)
    , '--autoaccept' # Accept all licenses
    , '--quiet-mode' # Unattended setup mode
)

echo "::group::Ensure package dir exists"
$pkg_dir = $env:INPUT_PACKAGE_DIR
$pkg_dir = $pkg_dir.Trim()
if ($pkg_dir) {
    echo "Creating local package directory: $pkg_dir"
    mkdir -Force $pkg_dir
    $args_ += '--local-package-dir'
    $args_ += $pkg_dir
}
else {
    echo "Using default package directory"
}
echo "::endgroup::"



$args_ += @(
    '--site', "$env:INPUT_SITE", # Download site
    '--root', "$env:INPUT_ROOT"  # Root installation directory
)
# '-P', '${{ env.Deps }}',
if ("$env:INPUT_UPGRADE_ALSO".ToLowerInvariant().Trim() -eq "true") {
    $args_ += '--upgrade-also'
}

echo "::group::Selected packages"
$packages = $env:INPUT_PACKAGES -Split '[,\s\\]+' -match '\S'
if ($packages.Count -gt 0) {
    $args_ += '--packages'  # Specify packages to install
    $args_ += $packages -Join (',')
}
$packages | Format-Table -Expand Both
echo "::endgroup::"

$args_ | Format-Table -Wrap -AutoSize
echo "::group::Run setup"
echo "Setup executable is $setup"
"Command to execute: & $setup $args_ | Out-Default"
& $setup $args_ | Out-Default
echo "::endgroup::"


# # $deps = '${ { inputs.packages } }'
# # # $depsList = $deps -split '\s+' -match '\S' | where {$_.Trim(',') -ne ''}
# # $depsList = $deps -split '\s+' -match '\S' | where {$_.Trim() -ne ''}
# # $depsList = $depsList | % { $_.Trim() }
# # $depsList = $depsList | % { $_.Trim(',') }
# # if ($depsList.Count -gt 0) {
# #   $args += '--packages'  # Specify packages to install
# #   $args += $depsList -Join(',')
# # }
# # $packages = '${ { inputs.packages } }'
# $packages = $env:pkgs
# $pkg_list = $packages.Split('', [System.StringSplitOptions]::RemoveEmptyEntries)
# echo "pkg_list is:"
# echo $pkg_list
# $pkg_list = $pkg_list | % { $_.Trim() }
# echo "pkg_list trim1 is:"
# echo $pkg_list
# $pkg_list = $pkg_list | % { $_.Trim('\') }
# echo "pkg_list trim2 is:"
# echo $pkg_list
# $pkg_list = $pkg_list | % { $_.Trim(',') }
# echo "pkg_list trim3 is:"
# echo $pkg_list
# if ($pkg_list.Count -gt 0) {
#     $args_ += '-P'
#     $args_ += $pkg_list -Join (',')
# }
# "Command to execute: & $setup $args_ | Out-Default"
# & $setup $args | Out-Default
# echo "::endgroup::"
# $env:pkgs = @"
#             cairo-devel
#             freetype-devel
#             gdal-devel
#             geos-devel
#             libjpeg-turbo-devel,  		  	     liblas-devel,
#             libpng-devel	,\
#             libpq-devel,\
#             libtiff-devel,\
#             netcdf-devel,	proj-devel,\
#             python3-core,\
#             python3-numpy,\
#             python3-ply	python3-pytest,\
#             python3-pywin32,\
#             python3-six,\
#             python3-wxpython,
#             sqlite3-devel, 
#             zstd-devel     
# "@
# $packages = $env:pkgs
# # $depslist2 = $packages -Split '\t'
# # $depslist2 = $packages -Split '[\s,]'
# # $depslist2 = $packages -Split '\s+'
# $depslist2 = $packages -Split '[,\s\\]+' -match '\S'
# $depslist2

# "xxxx"
# "yyyy"
# $depslist2 | Format-List

# "xxxx"
# "yyyy"
# $depslist2 | Get-Member

# "xxxx"
# "yyyy"
# , $depslist2 | Get-Member
# "xxxx"
# "yyyy"
# $depslist2 | Format-Table -AutoSize -RepeatHeader -Expand Both
# "xxxx"
# "yyyy"
# Format-Custom -InputObject $depslist2 -Expand Both
# "xxxx"
# "yyyy"
# $depslist2 | Format-List -Property *
# "xxxx"
# "yyyy"
# $depslist2 | ForEach-Object { New-Object PSObject -Property @{Item = $_ } } | Format-Table -AutoSize -Expand Both -Wrap
# "xxxx"
# "yyyy"
# $depslist2 | ForEach-Object { New-Object PSObject -Property @{
#         Index = $depslist2.IndexOf($_) 
#         Item  = $_
#     } } | Format-Wide -AutoSize -Expand Both
# "xxxx"
# "yyyy"
# $depslist2 | ForEach-Object { New-Object PSObject -Property @{
#         BItem  = $_
#         curr   = $depslist2.Current
#         AIndex = $depslist2.IndexOf($_) 
#     } } | Format-Table -Wrap
# "xxxx"
# "yyyy"
# $depslist2 | foreach { New-Object PSObject -Property @{
#         BItem  = $_
#         curr   = $depslist2.Current
#         AIndex = $depslist2.IndexOf($_) 
#     } } | Format-Table -Wrap 
# "xxxx"
# "yyyy"
# $result = foreach ($depslist2Item in $depslist2) {
#     # $foreach| Format-List -Expand Both
#     $foreach | Format-Table -Expand Both -Property *
#     New-Object PSObject -Property @{
#         BItem  = $depslist2Item
#         curr   = $foreach.Current
#         curr2  = $foreach
#         AIndex = $depslist2.IndexOf($depslist2Item) 
#     } 
    
# } 
# $result | Format-Table -Wrap 
# "www"
# foreach ($depslist2Item in $depslist2) {
#     # $foreach| Format-List -Expand Both
#     # $foreach| Format-Table -Expand  -Property *
#     # $foreach | Format-List -Property * 
#     $foreach | Get-Member -MemberType AliasProperty
#     # New-Object PSObject -Property @{
#     #     BItem=$depslist2Item
#     #     curr=$foreach.Current
#     #     curr2=$foreach
#     #     AIndex=$depslist2.IndexOf($depslist2Item) 
#     #     } 
    
# } 
# "wxyz"
# $result2 = for ($i = 0; $i -lt $depslist2.Count; $i++) {
#     <# Action that will repeat until the condition is met #>
#     New-Object PSObject -Property @{
#         Index = $i
#         Len   = $depslist2[$i].Length
#         Item  = $depslist2[$i]
#     } 
# }
# , $result2 | Format-Table -Wrap  -Expand Both -Property Index, Len, Item -AutoSize 


# $depslist2 | Select-Object -Property { ($_.Length) }   | Format-Table  -Expand Both
# # $depslist2 | Select-Object -Property {Len=$_.Length}   | Format-Table  -Expand Both
# $depslist2 | Format-Table  -Expand Both -Property @{Label = "Item"; Expression = { $_ } }
# $size = @{label = "Size(KB)"; expression = { $_.length / 1KB } }
# $depslist2 | Select-Object -Property  @{Label = "Item"; Expression = { $_ } }, @{Label = "Length"; Expression = { $_.Length } } 
# | Format-Table  -Expand Both 
# , ($depslist2 | Select-Object -Property  @{Label = "Item"; Expression = { $_ } }, @{Label = "Length"; Expression = { $_.Length } })
# | Format-Table  -Expand Both

