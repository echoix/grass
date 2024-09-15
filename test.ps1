$env:pkgs = @"
            cairo-devel
            freetype-devel
            gdal-devel
            geos-devel
            libjpeg-turbo-devel,  		  	     liblas-devel,
            libpng-devel	,\
            libpq-devel,\
            libtiff-devel,\
            netcdf-devel,	proj-devel,\
            python3-core,\
            python3-numpy,\
            python3-ply	python3-pytest,\
            python3-pywin32,\
            python3-six,\
            python3-wxpython,
            sqlite3-devel, 
            zstd-devel     
"@
$packages = $env:pkgs
# $depslist2 = $packages -Split '\t'
# $depslist2 = $packages -Split '[\s,]'
# $depslist2 = $packages -Split '\s+'
$depslist2 = $packages -Split '[,\s\\]+' -match '\S'
$depslist2

"xxxx"
"yyyy"
$depslist2 | Format-List

"xxxx"
"yyyy"
$depslist2 | Get-Member

"xxxx"
"yyyy"
, $depslist2 | Get-Member
"xxxx"
"yyyy"
$depslist2 | Format-Table -AutoSize -RepeatHeader -Expand Both
"xxxx"
"yyyy"
Format-Custom -InputObject $depslist2 -Expand Both
"xxxx"
"yyyy"
$depslist2 | Format-List -Property *
"xxxx"
"yyyy"
$depslist2 | ForEach-Object { New-Object PSObject -Property @{Item = $_ } } | Format-Table -AutoSize -Expand Both -Wrap
"xxxx"
"yyyy"
$depslist2 | ForEach-Object { New-Object PSObject -Property @{
        Index = $depslist2.IndexOf($_) 
        Item  = $_
    } } | Format-Wide -AutoSize -Expand Both
"xxxx"
"yyyy"
$depslist2 | ForEach-Object { New-Object PSObject -Property @{
        BItem  = $_
        curr   = $depslist2.Current
        AIndex = $depslist2.IndexOf($_) 
    } } | Format-Table -Wrap
"xxxx"
"yyyy"
$depslist2 | foreach { New-Object PSObject -Property @{
        BItem  = $_
        curr   = $depslist2.Current
        AIndex = $depslist2.IndexOf($_) 
    } } | Format-Table -Wrap 
"xxxx"
"yyyy"
$result = foreach ($depslist2Item in $depslist2) {
    # $foreach| Format-List -Expand Both
    $foreach | Format-Table -Expand Both -Property *
    New-Object PSObject -Property @{
        BItem  = $depslist2Item
        curr   = $foreach.Current
        curr2  = $foreach
        AIndex = $depslist2.IndexOf($depslist2Item) 
    } 
    
} 
$result | Format-Table -Wrap 
"www"
foreach ($depslist2Item in $depslist2) {
    # $foreach| Format-List -Expand Both
    # $foreach| Format-Table -Expand  -Property *
    # $foreach | Format-List -Property * 
    $foreach | Get-Member -MemberType AliasProperty
    # New-Object PSObject -Property @{
    #     BItem=$depslist2Item
    #     curr=$foreach.Current
    #     curr2=$foreach
    #     AIndex=$depslist2.IndexOf($depslist2Item) 
    #     } 
    
} 
"wxyz"
$result2 = for ($i = 0; $i -lt $depslist2.Count; $i++) {
    <# Action that will repeat until the condition is met #>
    New-Object PSObject -Property @{
        Index = $i
        Len   = $depslist2[$i].Length
        Item  = $depslist2[$i]
    } 
}
, $result2 | Format-Table -Wrap  -Expand Both -Property Index, Len, Item -AutoSize 


$depslist2 | Select-Object -Property { ($_.Length) }   | Format-Table  -Expand Both
# $depslist2 | Select-Object -Property {Len=$_.Length}   | Format-Table  -Expand Both
$depslist2 | Format-Table  -Expand Both -Property @{Label = "Item"; Expression = { $_ } }
$size = @{label = "Size(KB)"; expression = { $_.length / 1KB } }
$depslist2 | Select-Object -Property  @{Label = "Item"; Expression = { $_ } }, @{Label = "Length"; Expression = { $_.Length } } 
| Format-Table  -Expand Both 
,($depslist2 | Select-Object -Property  @{Label = "Item"; Expression = { $_ } }, @{Label = "Length"; Expression = { $_.Length } })
| Format-Table  -Expand Both

