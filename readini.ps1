# mkdir -Force "dl"
# Remove-Item "dl/*"
$pkg_dir = "./pkgd"
New-Item -ItemType "directory" -Path "$pkg_dir"
# mkdir -Force "$pkg_dir"
$site = "https://download.osgeo.org/osgeo4w/v2/"
$url = $site + "x86_64/setup.ini"
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
    # [PSCustomObject]$package = [PSCustomObject]@{}
    [hashtable]$package = [hashtable]@{}
    [string]$section = $null
    [string]$name = $null
    switch -Regex ($result2) {
        # '^setup-timestamp:\s+(.*)\s+$' { 
        '^setup-timestamp:\s*(.*)\s*' { 
            $ini["setup_timestamp"] = $Matches[1]
            # $ini.setup_timestamp = $Matches[1]
            continue
        }
        '^setup-version:\s*(.*)\s*' {
            # $ini.setup_version = $Matches[1]
            $ini["setup_version"] = $Matches[1]
            continue
        }  
        '^arch:\s*(.*)\s*' {
            $ini["arch"] = $Matches[1]
            continue
        } 
        '^release:\s*(.*)\s*' {
            $ini["release"] = $Matches[1]
            continue
        }
        '^skip:\s*(.*)\s*' {
            $ini["skip"] = $Matches[1]
            continue
        }    
        '^\@\s+(\S+)' {
            # $packageName, $section = $Matches[1], 'curr'
            $packageName, $section = $Matches[1], ''
            # $package = [PSCustomObject]@{ Name = $packageName } #@{Name = $packageName }
            $package = @{ Name = $packageName } #@{Name = $packageName }
            # $package = @{pName = $packageName }
            If ([string]::IsNullOrEmpty($ini["Packages"][$packageName]) -eq $true) {
                $ini["Packages"][$packageName] = $package #= @{Name = $packageName }
            }
            # If ([string]::IsNullOrEmpty($ini["Packages"][$packageName][$section]) -eq $true) { 
            #     $ini["Packages"][$packageName][$section] = @{ } 
            # }
            continue
        }
        '^\[([^\]]+)\]' {
            $section = $Matches[1]
            If ([string]::IsNullOrEmpty($ini["Packages"][$packageName][$section]) -eq $true) { 
                $ini["Packages"][$packageName][$section] = @{ } 
            }
            continue
        }
        '^([^:]+):\s*(.*)$' {
            $key = $Matches[1]
            $val = $Matches[2]
            # $package
            # $pack = $ini["Packages"][$packageName]
            # echo $package
            # $package += @{"$key" = $val } # [$key] = $val
            # $package += @{"$key" = $val } # [$key] = $val
            # $ini["Packages"][$packageName][$key] = $val
            # $ini["Packages"][$packageName][$key] = $val
            # $ini["Packages"][$packageName][$key] = $val
            if ($section -eq '') {
                # $ini["Packages"][$packageName][$key] = $val
                # $package = $ini["Packages"][$packageName]
                # $package.Add($key,$val)
                # $ini["Packages"][$packageName] = $package
                $ini["Packages"][$packageName][$key] = $val
            }
            else {
                $ini["Packages"][$packageName][$section][$key] = $val
            }
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
            continue
        }
        '^\[[^\]]+\]' {
            $section = $_
            continue
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

# "w3"
# $setupIniParsed
# # | Select-Object -First 15 
# # | Select-Object -First 15 
# | % { $_.Packages }
# | % { [pscustomobject]$_.Values}
# | % { [pscustomobject]$_}
# # | Select-Object  -Property Values
# # | Format-Table -Expand Both
# # | % { [PSCustomObject]$_.Value} 
# # | Format-List *
# # | Format-Table 
# | Format-List
# # | Format-Table *

# "w4"
# $setupIniParsed
# | Select-Object -First 15 
# # | ConvertTo-Json | Format-list 
# | Select-Object -Property * | ConvertTo-Json -Depth 5  | ConvertFrom-Json -AsHashtable | Format-Table
# | ConvertTo-Json | Format-Custom -Depth 4
# | ConvertTo-Xml | Format-Custom -Depth 3

# "w5"
# # $setupIniParsed.Packages.Values
# # $setupIniParsed.Packages.Values
# $setupIniParsed.Packages
# # | Select-Object -First 15 
# # | Get-Member -Name Packages
# # | % { $_.Packages | Select-Object -First 5 }
# # | % { $_.Packages.GetEnumerator() }
# # | Get-Member
# # | Select-Object -Property Value
# # | Select-Object -First 5 -Unique
# # | Select-Object -First 15 
# # | Select-Object -First 15 -Property Name
# # | % { $_.GetEnumerator() }
# | % { ($_.GetEnumerator() )}
# # | % { $_.GetEnumerator() | Sort-Object -Property key}
# # | % { [pscustomobject]$_.Values }
# # | % { $_.Values }
# # | % { [pscustomobject]$_ }
# # | Select-Object  -Property Values
# # | Format-Table -Expand Both
# # | % { [PSCustomObject]$_.Value} 
# | Format-List 
# # | Format-Table 
# # | Format-List
# # | Format-Table *

# "w6"
# # $setupIniParsed.Packages.Values
# [pscustomobject]($setupIniParsed.Packages)
# # | Select-Object -First 15 
# # | Get-Member -Name Packages
# # | % { $_.Packages | Select-Object -First 5 }
# # | % { $_.Packages.GetEnumerator() }
# # | Get-Member
# # | Select-Object -Property Value
# # | Select-Object -First 5 -Unique
# # | Select-Object -First 15 
# # | Select-Object -First 15 -Property Name
# # | % { $_.GetEnumerator() }
# # | % { ($_.GetEnumerator() )}
# # | % { $_.GetEnumerator() | Sort-Object -Property key}
# # | % { [pscustomobject]$_.Values }
# # | % { $_.Values }
# # | % { [pscustomobject]$_ }
# # | Select-Object  -Property Values
# # | Format-Table -Expand Both
# # | % { [PSCustomObject]$_.Value} 
# | Format-List 
# # | Format-Table 

# "w7"
# [pscustomobject]($setupIniParsed.Packages).GetEnumerator() 
# | Select-Object -Property Value 
# # | % { [PSCustomObject]$_.Members}
# # | Export-Csv -
# | Group-Object -Property {$_.Name} -NoElement
# # | Format-Table -Expand Both 

# "w8"
# $vars =[pscustomobject]($setupIniParsed.Packages).GetEnumerator() 
# # | Select-Object -Property Value 
# | Select-Object -Property Name,Value 
# | % { [PSCustomObject]$_}
# # | % { $_.Properties}
# # | Get-Member
# | % { $_.Value}
# # | % { [PSCustomObject]$_.Members}
# # | Export-Csv -
# # | Group-Object -Property {$_.Name} -NoElement
# # | Group-Object -Property {$_.Name} -NoElement -AsHashTable -AsString
# # | Group-Object -Property Name
# # | Group-Object -Property Name  -AsHashTable -AsString
# # | Group-Object -Property Name -NoElement -AsHashTable -AsString
# # | Format-Table -Expand Both 
# # | Format-Table 
# | Format-List
# # $vars.Value
# $vars

# "w9"
# $table = ([pscustomobject]($setupIniParsed.Packages.GetEnumerator() ))
# $table
# | ForEach-Object { $table['libmysql']}
# # | Select-Object -Property Value
# # | Select-Object -Property ( $table.Keys | Group-Object | Select-Object -ExpandProperty Name)
# # | ForEach-Object { [PSCustomObject]$_}
# # | Get-Member
# | Format-List -Expand Both 
# # | Format-Table -RepeatHeader 
# "w10"
# # $setupIniParsed.Packages
# # | %{$setupIniParsed.Packages[$_.Packages.Keys]}

# # $setupIniParsed.Packages.Keys | ForEach-Object { @($_)} | Format-Table
# # $setupIniParsed.Packages.Values | ForEach-Object { @($_)} | Format-Table
# # $setupIniParsed.Packages.Values | ForEach-Object { @($_)} | Format-List
# # $setupIniParsed.Packages.GetEnumerator().Values | Format-List
# # $setupIniParsed.Packages.GetEnumerator() | Format-List
# $setupIniParsed.Packages.GetEnumerator() 
# | Select-Object -Property Value
# # | % { @($_.Value)}
# | % { [psobject]$_ }
# | Format-List

# $arr1 = $setupIniParsed.Packages.GetEnumerator() 
# | Select-Object -Property Value
# # | % { @($_.Value)}
# | % { [psobject]$_ }

# , $arr1 | Format-Table -Expand Both


# function Flatten-Object ( $obj, [string] $prefix = "" ) {
#     [CmdletBinding()]

#     $res = @{}
#     Write-Verbose $prefix

#     if ($null -eq $obj) {
#         return @{$prefix = "null" }
#     } 

#     switch -Regex ($obj.GetType().Name ) {
#         '^(Boolean|String|Int32|Int64|Float|Double)$' {
#             $res += @{$prefix = $obj }
#         }
#         "Hashtable" {
#             $obj.GetEnumerator() | ForEach-Object {
#                 $res += Flatten-Object $_.Value ($prefix + "." + $_.Key)
#             }
#         }
#         '^(List.*|.+\[\])$' {
#             $i = 0
#             foreach ( $entry in $obj ) {
#                 $ind = $prefix + "[$i]"
#                 $res += Flatten-Object $entry $ind
#                 $i++
#             }
#         }
#     }
#     $res
# }

# # Flatten-Object -obj $setupIniParsed.Packages.Values
# # Show-Object 
# # $setupIniParsed.Packages.Values |%{$_ | out-string}
# # $setupIniParsed.Packages | % { $_ | Format-Table }
# # $setupIniParsed.Packages | % { $_ | Format-List }
# # $setupIniParsed.Packages.Values | % { $_ | Format-List }
# # $setupIniParsed.Packages.Values | % { $_ | Format-Table }
# # $setupIniParsed.Packages.Values | % { [pscustomobject]$_ | Format-Table }
# # $setupIniParsed.Packages.Values | % { [pscustomobject]$_ | Format-List }
# # $setupIniParsed.Packages.Values | Sort-Object -Property Name | % {[pscustomobject]$_ |Format-List }
# # $setupIniParsed.Packages.Values | Sort-Object -Property Name | % { [pscustomobject]$_ | Sort-Object | Format-List }
# $setupIniParsed.Packages.Values 
# | Sort-Object -Property Name 
# | % { [pscustomobject]($_) | Sort-Object
#     # [pscustomobject]$_ 
#     # | Sort-Object
#     # | [pscustomobject]$_
#     # | [pscustomobject]([ordered]$_) 
#     | Format-List 
# }
# # $setupIniParsed.Packages | % { [pscustomobject]$_ | % {[pscustomobject]($_.Value) | Format-List} }
# # $setupIniParsed.Packages | % { [pscustomobject]$_ | Format-List }
# # $setupIniParsed.Packages.GetEnumerator() |%{$_ | out-string}


# $setupIniParsed.Packages.Values | Sort-Object -Property Name | % { [pscustomobject]($_) | Sort-Object | Format-List }
$siteFolderTarget = 'https%3a%2f%2fdownload.osgeo.org%2fosgeo4w%2fv2%2f'
$siteFolderTarget
$siteFolder = [URI]::EscapeDataString(($site)).ToLower()
$siteFolder

$pkgListAsked = @(
    'cairo-devel', 'freetype-devel', 'gdal-devel', 'geos-devel', 'libjpeg-turbo-devel', 'liblas-devel', 'libpng-devel', 'libpq-devel', 'libtiff-devel', 'netcdf-devel', 'proj-devel', 'python3-core', 'python3-numpy', 'python3-ply', 'python3-pytest', 'python3-pywin32', 'python3-six', 'python3-wxpython', 'sqlite3-devel', 'zstd-devel'
)
$pkgListAdded = @()
$pkgListToAdd = @()
# $pkgListAsked | % { $pkgListToAdd += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') } | Out-Null
$pkgListAdded += $pkgListAsked | % { $setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S' } | Sort-Object | Get-Unique
$pkgListAdded.Length
$i = 0
$prevLength = $pkgListAdded.Length

while ($i -lt 5) {
    $pkgListAdded = $pkgListAdded + ($pkgListAdded | Sort-Object | Get-Unique | % { $setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S' }) | Sort-Object | Get-Unique
    if ($pkgListAdded.Length -le $prevLength) {
        break
    }
    $prevLength = $pkgListAdded.Length
    $i++
}
"i is $i"
# $pkgListAdded = $pkgListAdded + ($pkgListAdded | Sort-Object | Get-Unique | % { $setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S' }) | Sort-Object | Get-Unique
# # $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded.Length
# $pkgListAdded += $pkgListAdded | Sort-Object | Get-Unique  | % { $setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S' } | Sort-Object | Get-Unique
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded.Length
# $pkgListToAdd = $pkgListToAdd | Sort-Object | Get-Unique
# $pkgListAdded += $pkgListToAdd
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListToAdd = @()
$pkgListAdded
$pkgListAdded.Length

# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# $pkgListAdded | % { $pkgListAdded += ($setupIniParsed.Packages[$_]['requires'] -split '\s+' -match '\S') }
# $pkgListAdded = $pkgListAdded | Sort-Object | Get-Unique
# $pkgListAdded
# $pkgListAdded.Length
# Write-host([URI]::EscapeDataString(($site)))

# D:/OSGeo4W_pkg/http%3a%2f%2fdownload.osgeo.org%2fosgeo4w%2fv2%2f/x86_64/release/freetype/freetype-devel/freetype-devel-2.13.2-1.tar.bz2
# https%3A%2F%2Fdownload.osgeo.org%2Fosgeo4w%2Fv2%2F


# $pkgListAdded | Sort-Object -Property @{name='Size';Expression={$setupIniParsed.Packages[$_]['install']}}
# $pkgListAdded | Get-Member
$pkgs = $pkgListAdded 
| Select-Object -Property @{n = 'Name'; e = { $_ } }, @{Name = 'install'; Expression = { ($setupIniParsed.Packages[$_]['install'] -split '\s+') } }
| Select-Object -Property Name, @{Name = 'Size'; Expression = { [Int] $_.'install'[1] } }, @{n = "Url"; e = { $_.'install'[0] } }, @{n = "Digest"; e = { $_.'install'[2] } }
| Select-Object -Property *, @{Name = "Uri"; Expression = { [System.Uri]("$site/$($_.Url)" ) } }, @{Name = "OutFile"; Expression = { $pkg_dir + '/' + $siteFolder + $_.Url } }
| Sort-Object -Property Name
| Sort-Object -Property Size -Descending
# $pkgListAdded | Select-Object -Property @{name='Size';Expression={($setupIniParsed.Packages[$_]['install'] -split'\s+')[1]}}

$pkgs

# $files = @(
#     @{
#         Uri     = "$baseUri/v7.3.0-preview.5/PowerShell-7.3.0-preview.5-win-x64.msi"
#         OutFile = 'PowerShell-7.3.0-preview.5-win-x64.msi'
#     },
#     @{
#         Uri     = "$baseUri/v7.3.0-preview.5/PowerShell-7.3.0-preview.5-win-x64.zip"
#         OutFile = 'PowerShell-7.3.0-preview.5-win-x64.zip'
#     },
#     @{
#         Uri     = "$baseUri/v7.2.5/PowerShell-7.2.5-win-x64.msi"
#         OutFile = 'PowerShell-7.2.5-win-x64.msi'
#     },
#     @{
#         Uri     = "$baseUri/v7.2.5/PowerShell-7.2.5-win-x64.zip"
#         OutFile = 'PowerShell-7.2.5-win-x64.zip'
#     }
# )
# $files = $pkgs | Sort-Object -Property Size -Descending | Select-Object -Property Uri, OutFile | Out-String
# $files
$jobs = @()

Measure-Command {


foreach ($file in $pkgs) {
# foreach ($file in $files) {
    # mkdir -Force 
    $jobs += Start-ThreadJob -Name $file.OutFile -ScriptBlock {
        $params = $using:file
        New-Item -ItemType "directory" -Path (Split-Path -Parent $params.OutFile)
        # New-Item -Path "c:\" -Name "logfiles" -ItemType "directory"
        # mkdir -Force (Split-Path -Parent $params.OutFile)
        $params2 = @{Uri = $params.Uri; OutFile = $params.OutFile }
        Invoke-WebRequest @params2
    }
}

Write-Host "Downloads started..."
Wait-Job -Job $jobs

foreach ($job in $jobs) {
    Receive-Job -Job $job
}
}