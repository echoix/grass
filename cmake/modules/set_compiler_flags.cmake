macro(set_compiler_flags)
    set(GRASS_COMPILE_DEFINITIONS GRASS_CMAKE_BUILD=1)
    if(MSVC)
        list(APPEND GRASS_COMPILE_DEFINITIONS _CRT_SECURE_NO_WARNINGS NOMINMAX)
    endif()

    add_compile_definitions(${GRASS_COMPILE_DEFINITIONS})
endmacro()
