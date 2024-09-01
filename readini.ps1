# mkdir -Force "dl"
# Remove-Item "dl/*"

$url = "https://download.osgeo.org/osgeo4w/v2/x86_64/setup.ini"
# Measure-Command { Invoke-WebRequest -Uri $url -OutFile "dl/" }
iwr -Uri $url -OutFile "setup.ini"


Function Load-IniFile ([string]$Inputfile, [PSCustomObject]$ExistingHashTable = $null) {
    # [string]   $comment = ";"
    # [string]   $header = "^\s*(?!$($comment))\s*\[\s*(.*[^\s*])\s*]\s*$"
    # [string]   $item = "^\s*(?!$($comment))\s*([^=]*)\s*=\s*(.*)\s*$"
    [string]   $comment = "#"
    [string]   $packagePat = "^\s*(?!$($comment))\s*\@\s\s*(.*[^\s*])\s*$"
    [string]   $header = "^\s*(?!$($comment))\s*\[\s*(.*[^\s*])\s*]\s*$"
    [string]   $item = "^\s*(?!$($comment))\s*([^=]*)\s*=\s*(.*)\s*$"
    # [hashtable]$ini = @{Packages = @{}}
    [PSCustomObject]$ini = [PSCustomObject]@{Packages = @{} }
    If ($ExistingHashTable -ne $null) { $ini = $ExistingHashTable.Clone() }

    If ((Test-Path -LiteralPath $inputfile) -eq $False) { Write-Warning "Load-IniFile: Path not found: $inputfile"; Return $null }

    [string]$name = $null
    [string]$section = $null
    [string]$package = $null
    Switch -Regex -File $inputfile {
        "$($packagePat)" {
            [string]$package = (($matches[1] -replace ' ', '_').Trim().Trim("'"))
            If ($package.StartsWith('com') -eq $true) { $package = "tol$($package.Substring(3))" }
            If ([string]::IsNullOrEmpty($ini.Packages[$package]) -eq $true) { $ini.Packages[$package] = @{} }
            # If ([string]::IsNullOrEmpty($ini.Packages[$package]) -eq $true) { $ini.Packages[$package] = [PSCustomObject]@{Name = $null; sdesc = $null } }
        }
        "$($header)" {
            [string]$section = (($matches[1] -replace ' ', '_').Trim().Trim("'"))
            If ($section.StartsWith('com') -eq $true) { $section = "tol$($section.Substring(3))" }
            If ([string]::IsNullOrEmpty($ini.Packages[$package][$section]) -eq $true) { $ini.Packages[$package][$section] = @{ } }
            # If ([string]::IsNullOrEmpty($ini.Packages[$package][$section]) -eq $true) { $ini.Packages[$package][$section] = [PSCustomObject]@{Name = $null; sdesc = $null } }
        }
        "$($item)" {
            [string]$name, $value = $matches[1..2]
            If (([string]::IsNullOrEmpty($name) -eq $False) -and ([string]::IsNullOrEmpty($section) -eq $False)) {
                $value = (($value -split '    #')[0]).Trim()    # Remove any comments
                If ($inputfile.Contains('\settings\') -eq $False) { $value = $value.Trim("'") }
                $ini.Packages[$package][$section][$name.Trim()] = ($value.Replace('`n', "`n"))
            }
        }
    }
    Return $ini
}

function Load-OSGeo4WSetupIni (
    [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
    [string]
    $Input,
    [hashtable]$ExistingHashTable = $null
    # [PSCustomObject]$ExistingHashTable = $null
) {
    # [PSCustomObject]$ini = [PSCustomObject]@{Packages = $packages; setup_timestamp = $null; }
    # [PSCustomObject]$ini = [PSCustomObject]@{ }
    [hashtable]$ini = [hashtable]@{ }
    If ($ExistingHashTable -ne $null) { $ini = $ExistingHashTable.Clone() }
    # [PSCustomObject]$packages = [PSCustomObject]@{ }
    If ([string]::IsNullOrEmpty($ini["Packages"]) -eq $true) { $ini["Packages"] = @{} }

   
    $result2 = $Input -split '\r?\n' 
    | ForEach-Object { $_ -replace '#.*$', '' -replace '^\s+', '' }
    | ForEach-Object { $_ -replace '(\S)\s+$', '$1' }
    [string]$packageName = $null
    [string]$package = @{}
    [string]$section = $null
    [string]$name = $null
    switch -Regex ($result2) {
        # '^setup-timestamp:\s+(.*)\s+$' { 
        '^setup-timestamp:\s*(.*)\s*' { 
            $ini["setup_timestamp"] = $Matches[1]
            # $ini.setup_timestamp = $Matches[1]
        }
        '^setup-version:\s*(.*)\s*' {
            # $ini.setup_version = $Matches[1]
            $ini["setup_version"] = $Matches[1]
        }  
        '^arch:\s*(.*)\s*' {
            $ini["arch"] = $Matches[1]
        } 
        '^release:\s*(.*)\s*' {
            $ini["release"] = $Matches[1]
        }
        '^skip:\s*(.*)\s*' {
            $ini["skip"] = $Matches[1]
        }    
        '^\@\s+(\S+)' {
            $packageName, $section = $Matches[1], ''
            $package = @{pName=$packageName}
            If ([string]::IsNullOrEmpty($ini["Packages"][$packageName]) -eq $true) {
                $ini["Packages"][$packageName] = $package = @{Name=$packageName}
            }
            If ([string]::IsNullOrEmpty($ini["Packages"][$packageName][$section]) -eq $true) { 
                $ini["Packages"][$packageName][$section] = @{ } 
            }
        }
        '^([^:]+):\s*(.*)$' {
            $key = $Matches[1]
            $val = $Matches[2]
            # $ini["Packages"][$packageName][$key] = $val
            # $ini["Packages"][$packageName][$key] = $val
            # $ini["Packages"][$packageName][$section][$key] = $val
            # my $key = $1;
            # my $val = $2;
            # if ($key !~ /^(?:prev|curr|test)/) {
            #     $pkg{$pname}{$what}{$key} = get(\*F, $key, $val);
            # } else {
            #     if ($key eq 'curr') {
            #         $key = '';
            #     } else {
            #         $key = "[$key]\n";
            #     }
            #     $pkg{$pname}{$key}{'version'} = $val;
            # }
            # next if defined $val;
        }    
        Default {}
    }
  
    # $result2 | Select-String -Pattern '^setup-timestamp:'

    # # $var2  -replace '#.*$', '' -replace '^\s+', ''
    # $var2 -split '\r?\n' -replace '#.*$', '' -replace '^\s+', ''
    # # | Select-String -Pattern '(\S)\s+$'
    # | ForEach-Object { $_ -replace '(\S)\s+$', '$1' }
    # | ForEach-Object { [PSCustomObject]@{ len = $_.Length; val = $_ } }
    # | Select-Object -First 20 
    # | Format-Table

    # $result2 = $result | % { $_.Replace('(#.*)$', '') }
    # |  -replace '^\s+',''
    Return $ini
}
# $parsed = Load-IniFile -Inputfile "setup.ini"

# # $parsed | Sort-Object -Property 
# # $parsed | Format-Table -RepeatHeader -Expand Both 
# $parsed.Packages | Format-Table -RepeatHeader -Expand Both 
# # $parsed | Format-Table -RepeatHeader -Expand Both -AutoSize
# # $parsed | Format-List -Expand Both
# $parsed.Packages | Format-List  -Expand Both 




# $setupIniParsed = iwr -Uri $url |  Load-OSGeo4WSetupIni 
# Get-Member -InputObject $setupIniParsed
# $setupIniParsed |  Get-Content -Head 15

# iwr -Uri $url |Out-String -Stream| Format-table
# iwr -Uri $url | Select-String -NotMatch '#.*$' | Format-table
# iwr -Uri $url | Select-String -NotMatch '#.*$' -AllMatches | Get-Content -Head 15| Format-List 
# iwr -Uri $url | Select-String -NotMatch '#.*$' -AllMatches
# iwr -Uri $url | Select-String -Pattern '#.*$' 
# iwr -Uri $url | Select-Object -Expand Content | Out-String  | Get-Content -PipelineVariable Content -Head 15 #| Select-String -Pattern '#.*$' 
# iwr -Uri $url | Select-Object -Expand Content | Out-String -Stream | Get-Content -Head 15 #| Select-String -Pattern '#.*$' 
#  Out-String -Stream
# iwr -Uri $url | Select-Object -Expand Content | Get-Content -PipelineVariable Content -Head 15 #| Select-String -Pattern '#.*$' 
# iwr -Uri $url | Select-Object -Expand Content | Format-List -Expand EnumOnly
# iwr -Uri $url | Select-Object -Expand Content
# $var = iwr -Uri $url | Select-Object -ExpandProperty Content
# $var = iwr -Uri $url | Select-Object -Expand Content
# $var = iwr -Uri $url | Select-Object -Expand Content
# $var = iwr -Uri $url | Select-Object -Property Content
# $var = iwr -Uri $url #| Select-Object -Property Content
# $var | Format-List -Expand EnumOnly
# ,$var | Format-List -Expand CoreOnly
# ,$var | Format-List -Expand Both | Get-Content 
# $var | Get-Member -Name Content | Select-String -Pattern "#.*$"
# ,$var | Format-List -Expand Both 
# $var -split '\r?\n'  | Select-String -Pattern "(#.*)$" -List
# $var -split '\r?\n'  | Select-String -Pattern "(#.*)$"
# $var -split '\r?\n'  | Select-String -Pattern "(#.*)$" -AllMatches | Out-String |  Get-Content -Head 15 -AsByteStream
# $var -split '\r?\n'  | Select-String -Pattern "(#.*)$" -AllMatches |  Get-Content -Head 15 -AsByteStream
# $var -split '\r?\n'  | Select-String -Pattern "(#.*)$" -AllMatches
# $var -split '\r?\n'  | Select-String -NotMatch "#.*$" |  Get-Content -Head 15 
# $var -split '\r?\n'  | Select-String -NotMatch "#.*$" |  Get-Content -Head 15 
# $var -split '\r?\n'
# # | Select-String -NotMatch "(#.*)$" -AllMatches 
# # | Select-String -NotMatch "#.*$" -AllMatches 
# | Select-String -NotMatch "#.*$" 
# | Select-String -NotMatch "^\s+"
# # | Select-String -Pattern "^[^@].*@.*"
# # | % { $_ -replace '(\S)\s+$', '$1' }
# | ForEach-Object { [PSCustomObject]@{ len = $_.Length; val = $_ } }
# | Select-Object -First 15 
# | Format-Table
# $var -split '\r?\n' -replace '#.*$', '' -replace '^\s+', '' -replace '(\S)\s+$', '$1'
# $var -split '\r?\n' -replace '#.*$', '' -replace '^\s+', '' -replace '(\S)\s+$', '$2'
# $var -split '\r?\n' -replace '#.*$', '' -replace '^\s+', '' 

# $var -split '\r?\n' -replace '#.*$', '' -replace '^\s+', '' 
# | Select-String -Pattern '(\S)\s+$'
# # | % { $_ -replace '(\S)\s+$', '$1' }
# | ForEach-Object { [PSCustomObject]@{ len = $_.Length; val = $_ } }
# | Select-Object -First 20 
# | Format-Table


$var2 = Get-Content "./setup2.ini"

# # $var2  -replace '#.*$', '' -replace '^\s+', ''
# $var2 -split '\r?\n' -replace '#.*$', '' -replace '^\s+', ''
# # | Select-String -Pattern '(\S)\s+$'
# | ForEach-Object { $_ -replace '(\S)\s+$', '$1' }
# | ForEach-Object { [PSCustomObject]@{ len = $_.Length; val = $_ } }
# | Select-Object -First 20 
# | Format-Table

"w1"
# $var2 | Load-OSGeo4WSetupIni 
$setupIniParsed = Get-Content -Raw './setup2.ini' | Load-OSGeo4WSetupIni 
$setupIniParsed | Select-Object -First 15 
# | ForEach-Object { [PSCustomObject]@{ len = $_.Length; val = $_ } }
| Format-Table

# $setupIniParsed.Packages | Select-Object -First 15 -ExpandProperty
# | Format-Table
# # | Format-List 

# $setupIniParsed | Select-Object -First 15 -ExpandProperty Packages
# | Select-Object  -Property Values
# # | Format-Table -Expand Both
# # | % { [PSCustomObject]@{}} 
# | Format-List 
# $setupIniParsed.Packages.Keys
# # | Select-Object -First 15 -ExpandProperty Packages
# # | Select-Object  -Property Values
# # | Format-Table -Expand Both
# # | % { [PSCustomObject]@{}} 
# | Format-List

"w3"
$setupIniParsed
# | Select-Object -First 15 
# | Select-Object -First 15 
| % { $_.Packages }
| % { [pscustomobject]$_.Values}
| % { [pscustomobject]$_}
# | Select-Object  -Property Values
# | Format-Table -Expand Both
# | % { [PSCustomObject]$_.Value} 
# | Format-List *
# | Format-Table 
| Format-List
# | Format-Table *