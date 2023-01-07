cmake_minimum_required(VERSION 3.24)
project(GRASS VERSION 8.3.0 LANGUAGES C CXX)
#CMAKE_LINK_LIBRARIES_ONLY_TARGETS at top level


#add_library(Toolchain::m INTERFACE IMPORTED)
#set_target_properties(Toolchain::m PROPERTIES
#           IMPORTED_LIBNAME "m"
#        )
#target_link_libraries(App PRIVATE Toolchain::m)

## Better: separate paths for build and install, with the latter added
## as part of the install() command rather than with the target
#include(GNUInstallDirs)
#target_include_directories(Foo
#           PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
#        )
#install(TARGETS Foo ...
#           INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
#        )

include(GNUInstallDirs)
include(cmake/IncludeCheck.cmake)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/include/grass/version.h.in
        "${CMAKE_CURRENT_BINARY_DIR}/include/grass/version.h")

message(STATUS "Creating ${CMAKE_CURRENT_BINARY_DIR}/include/grass/config.h")

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/include/grass/config.h.cmake.in
        "${CMAKE_CURRENT_BINARY_DIR}/include/grass/config.h")

#add_subdirectory(include)
add_subdirectory(lib)

# If we are being built inside another project,
# ie: we are a package included in another, we won't need
# to build everything.
# In the other case, the optional steps are here
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    cmake_minimum_required(VERSION 3.24)
    option(GRASS_BUILD_TESTS      "whether or not tests should be built" ON)
    option(GRASS_BUILD_PACKAGE    "whether or not the package should be built" ON)
    option(GRASS_ENABLE_INSTALL   "whether or not to enable the install rule" ON)


#    install(EXPORT GRASS NAMESPACE GRASS::)
endif()
