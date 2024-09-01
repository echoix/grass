mkdir -Force "dl"
Remove-Item "dl/*"
$url = "https://download.osgeo.org/osgeo4w/v2/x86_64/release/proj/proj-data/proj-data-1.17-1.tar.bz2"
$destCurl = "dl/curl-proj-data-1.17-1.tar.bz2"
$destIwr1 = "dl/iwr1-proj-data-1.17-1.tar.bz2"
$destIwr2 = "dl/iwr2-proj-data-1.17-1.tar.bz2"
$destBits = "dl/bits-proj-data-1.17-1.tar.bz2"
# Set-PSDebug -Trace 1
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