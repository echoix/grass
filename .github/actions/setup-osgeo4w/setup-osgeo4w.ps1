"::group::Download OSGeo4W installer"
$exe = 'osgeo4w-setup.exe'
$url = $env:INPUT_SITE + $exe
$setup = '.\' + $exe
echo "Starting download of $url..."
Invoke-WebRequest $url -OutFile $setup
echo "Download completed"
"::endgroup::"

# Array to store arguments to pass to the installer
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

    # add arguments
    $args_ += '--local-package-dir'
    $args_ += $pkg_dir
}
else {
    echo "Using default package directory"
}
echo "::endgroup::"

# add arguments
$args_ += @(
    '--site', "$env:INPUT_SITE", # Download site
    '--root', "$env:INPUT_ROOT"  # Root installation directory
)
if ("$env:INPUT_UPGRADE_ALSO".ToLowerInvariant().Trim() -eq "true") {
    $args_ += '--upgrade-also'
}

echo "::group::Selected packages"
$packages = @()
$packages += "$env:INPUT_PACKAGES".ToString() -Split '[,\s\\]+' -match '\S'
if ($packages.Count -gt 0) {
    $args_ += '--packages' # Specify packages to install
    $args_ += $packages -Join (',')
}
# Use comma to show information of the collection itself in the header
, $packages | Format-Table -Expand Both
echo "::endgroup::"


echo "::group::Run setup"
echo "Setup executable is $setup"
"Command to execute: & $setup $args_ | Out-Default"
& $setup $args_ | Out-Default
echo "::endgroup::"
