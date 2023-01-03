macro(set_compiler_flags)
  if(MSVC)
    set(GRASS_C_FLAGS
        "/D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /DGRASS_CMAKE_BUILD=1"
    )
    set(GRASS_CXX_FLAGS "${GRASS_C_FLAGS}")
  else()
    set(GRASS_C_FLAGS "-DGRASS_CMAKE_BUILD=1")
    set(GRASS_CXX_FLAGS "${GRASS_C_FLAGS}")
  endif()

  set(CMAKE_CXX_FLAGS "${GRASS_CXX_FLAGS} ${CMAKE_CXX_FLAGS}")
  set(CMAKE_C_FLAGS "${GRASS_C_FLAGS} ${CMAKE_C_FLAGS}")

endmacro()
