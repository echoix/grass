#add_library(grass_datetime INTERFACE)
add_subdirectory(datetime)
add_subdirectory(gis)

install(EXPORT GRASS_grasslibs DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/GrassLibs NAMESPACE GRASS:: COMPONENT Libs)