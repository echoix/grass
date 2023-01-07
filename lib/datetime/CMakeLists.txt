add_library(grass_datetime
        between.c change.c copy.c diff.c error.c format.c
        incr1.c incr2.c incr3.c local.c misc.c same.c scan.c sign.c type.c tz1.c tz2.c values.c
#        grass/datetime.h
        )
add_library(GRASS::datetime ALIAS grass_datetime)
#set_target_properties(grass_datetime PROPERTIES EXPORT_NAME GRASS::datetime)
#set_target_properties( grass_datetime PROPERTIES FRAMEWORK TRUE PUBLIC_HEADER grass/datetime.h)
target_sources(grass_datetime
           PUBLIC
               FILE_SET installed_headers
               TYPE HEADERS
               BASE_DIRS
                ${GRASS_SOURCE_DIR}/include
#        ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass
        FILES ${GRASS_SOURCE_DIR}/include/grass/datetime.h
        )
#target_sources(grass_datetime
#           PUBLIC
#               FILE_SET installed
#               TYPE HEADERS
#               BASE_DIRS
#                grass
#        ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass
##        include
##        ${CMAKE_CURRENT_BINARY_DIR}/../../include
##        ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass
#        FILES grass/datetime.h
#        )

#set_target_properties(grass_datetime PROPERTIES PUBLIC_HEADER ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass/datetime.h)
#target_include_directories(grass_datetime PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../../include/)
#target_include_directories(grass_datetime PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass/datetime.h)
#set_target_properties(grass_datetime PROPERTIES FRAMEWORK TRUE PUBLIC_HEADER ${CMAKE_CURRENT_SOURCE_DIR}/../../include)
#target_sources(grass_datetime INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/../../include)
#target_sources(grass_datetime INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass/datetime.h)

#target_sources(grass_datetime
#           PUBLIC
#               FILE_SET installed
#               TYPE HEADERS
#               BASE_DIRS
#                include/grass
#        ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass
##        include
##        ${CMAKE_CURRENT_BINARY_DIR}/../../include
##        ${CMAKE_CURRENT_SOURCE_DIR}/../../include/grass
#               FILES include/grass/datetime.h
##           PRIVATE
##               FILE_SET internal
##               TYPE HEADERS
##               BASE_DIRS private
##               FILES private/colors_impl.h
#        )

target_include_directories(grass_datetime
           PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>
        )
install(TARGETS grass_datetime
        EXPORT GRASS_grasslibs
        DESTINATION ${CMAKE_INSTALL_LIBDIR}
        COMPONENT grasslibs
        RUNTIME
        LIBRARY
        ARCHIVE
        FILE_SET installed_headers
           INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}

        )
#install(EXPORT GRASS NAMESPACE GRASS::LIBS)