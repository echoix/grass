#!/bin/sh

set -e

if [ "$CI" ] ; then
	HostArch="x64"
	Arch="x64"
	vctoolsBinPath='C:/Program Files (x86)\Microsoft Visual Studio/2019/Enterprise/VC/Tools/MSVC/14.29.30133/bin/HostX64/x64/'
	echo "Calling vswhere"
	"${ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe" -? || true
	# Adapted the usage examples of vswhere for bash, and our specific needs: https://github.com/microsoft/vswhere/wiki/Find-VC
	installDir="$("${ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe" -latest -products "*" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath)"
	echo "installDir is: $installDir"
	if [ -d "$installDir" ]; then
		versionFilePath="${installDir}/VC/Auxiliary/Build/Microsoft.VCToolsVersion.default.txt"
		if [ -f "$versionFilePath" ]; then
			versionContents=$(cat "${versionFilePath}")
			echo "Default VCToolsVersion is: '$versionContents'"
			vctoolsBinPath="${installDir}/VC/Tools/MSVC/${versionContents}/bin/Host${HostArch}/${Arch}/"
		fi
	fi
	vctoolsBinPathMsys="$(cygpath -ua "$vctoolsBinPath")"
	# dumpbin in GH actions moved to sub-directory
	# export PATH="$PATH:$(cygpath -ua 'C:/Program Files (x86)\Microsoft Visual Studio/2019/Enterprise/VC/Tools/MSVC/14.29.30133/bin/HostX64/x64/')"
	export PATH="$PATH:${vctoolsBinPathMsys}"
	# dumpbin in GH actions does not support options starting with "-"
	DUMPBIN_EXPORT="/EXPORTS"
else
	DUMPBIN_EXPORT="-exports"
fi

[ -d mswindows/osgeo4w/vc ] || mkdir mswindows/osgeo4w/vc

if [ -n "$VCPATH" ]; then
	PATH=$PATH:$VCPATH
fi

for dllfile in "$@"; do
	dlldir=${dllfile%/*}
	dllfile=${dllfile##*/}

	dllbase=${dllfile%.dll}
	dllname=${dllbase#lib}
	dllname=${dllname%.$VERSION}
	defname=$dllname.def
	libname=$dllname.lib

 	echo "$dllfile => $dllname"

	(cd $dlldir; dumpbin "$DUMPBIN_EXPORT" $dllfile) |
		sed -nf mswindows/osgeo4w/mklibs.sed |
		egrep -v "^[	 ]*(_+IMPORT_DESCRIPTOR_.*|_+NULL_IMPORT_DESCRIPTOR)$" >mswindows/osgeo4w/vc/${defname%$VERSION}

	(cd mswindows/osgeo4w/vc ;
	    lib -nologo -def:${defname} -subsystem:windows -machine:x64
	    lib -nologo $libname || exit)
done
