mkdir -Force "dl"
Remove-Item "dl/*"
$url = "https://download.osgeo.org/osgeo4w/v2/x86_64/release/proj/proj-data/proj-data-1.17-1.tar.bz2"
$destWc = "dl/wc-proj-data-1.17-1.tar.bz2"
$destCurl = "dl/curl-proj-data-1.17-1.tar.bz2"
$destIwr1 = "dl/iwr1-proj-data-1.17-1.tar.bz2"
$destIwr2 = "dl/iwr2-proj-data-1.17-1.tar.bz2"
$destBits = "dl/bits-proj-data-1.17-1.tar.bz2"
# Set-PSDebug -Trace 1
Measure-Command { 
    $wc = [System.Net.WebClient]::new()
    $wc.DownloadFile($url, $destWc)
    # $pkgurl = 'https://github.com/PowerShell/PowerShell/releases/download/v6.2.4/powershell_6.2.4-1.debian.9_amd64.deb'
    # $publishedHash = '8E28E54D601F0751922DE24632C1E716B4684876255CF82304A9B19E89A9CCAC'
    # $FileHash = Get-FileHash -InputStream ($wc.OpenRead($pkgurl))
    # $FileHash.Hash -eq $publishedHash 
}

'Measure-Command { Invoke-WebRequest -Uri $url -OutFile $destIwr1 }'
Measure-Command { Invoke-WebRequest -Uri $url -OutFile $destIwr1 }
'Measure-Command { curl -o $destCurl $url }'
Measure-Command { curl -o $destCurl $url }
Import-Module BitsTransfer
'Measure-Command { Start-BitsTransfer -Source $url -Destination $destBits }'
Measure-Command { Start-BitsTransfer -Source $url -Destination $destBits }
$ProgressPreference = 'SilentlyContinue'
'Measure-Command { Invoke-WebRequest -Uri $url -OutFile $destIwr2 }'
Measure-Command { Invoke-WebRequest -Uri $url -OutFile $destIwr2 }
$ProgressPreference = 'Continue'