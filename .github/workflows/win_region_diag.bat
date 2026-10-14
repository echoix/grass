set grass=%1
set python=%2

call %grass% --tmp-project XY --exec g.download.project url=https://grass.osgeo.org/sampledata/north_carolina/nc_spm_full_v2beta1.tar.gz path=%USERPROFILE%
%python% -m pip install pefile
call %grass% --tmp-mapset %USERPROFILE%\nc_spm_full_v2beta1 --exec %python% .github\workflows\win_region_diag.py
